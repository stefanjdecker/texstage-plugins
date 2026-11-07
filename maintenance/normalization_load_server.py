# SPDX-License-Identifier: Apache-2.0
"""Loopback-only instrumented server; wrappers observe unmodified runtime calls.

No production endpoint, queue limit, lease, hook deadline or policy is changed.
Metrics contain synthetic job IDs and durations, never authentication tokens,
answers or private authoring data. Hook wall times include serialization/IPC;
the first call also includes provider subprocess startup.
"""
import argparse
import json
import time
import sys
import threading
from pathlib import Path

import uvicorn
from texstage.plugins.catalog import discover
from texstage.plugins.policy import enable
from texstage.plugins.runtime import Runtime
from texstage.plugins.worker import Workers
from texstage.server.app import ServerConfig, create_app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--port", type=int, default=18835)
    args = parser.parse_args()
    args.metrics.parent.mkdir(parents=True, exist_ok=True)
    output = args.metrics.open("w", encoding="utf-8", buffering=1, newline="\n")
    start = time.perf_counter()

    def emit(kind, **fields):
        output.write(json.dumps({"event": kind, "ms": (time.perf_counter() - start) * 1000, **fields}) + "\n")

    original_hook = Workers.call

    def hook(self, cid, method, *values):
        before = time.perf_counter()
        error = None
        try:
            return original_hook(self, cid, method, *values)
        except Exception as exc:
            error = type(exc).__name__
            raise
        finally:
            emit("hook", method=method, duration_ms=(time.perf_counter() - before) * 1000, error=error)

    Workers.call = hook
    for method in ("command", "lease", "finish"):
        original = getattr(Runtime, method)

        def wrapped(self, *values, _method=method, _original=original, **kwargs):
            before = time.perf_counter()
            result = _original(self, *values, **kwargs)
            details = {"duration_ms": (time.perf_counter() - before) * 1000}
            if _method == "command":
                envelope = values[3]
                details.update(item=envelope["item"], operation=envelope["operation"],
                               request=envelope["request_id"], receipt=result)
            elif _method == "lease":
                details["jobs"] = [{"id": job["id"], "generation": job["generation"]} for job in result]
            else:
                details.update(id=values[2]["id"], generation=values[2]["generation"],
                               outcome=values[2]["outcome"]["status"], accepted=result)
            emit(_method, **details)
            return result

        setattr(Runtime, method, wrapped)
    original_commit = Runtime._commit

    def committed(self, row, transition, **kwargs):
        result = original_commit(self, row, transition, **kwargs)
        jid = kwargs.get("delivery")
        if jid:
            job = self.db.execute("SELECT status,delivered,generation,result FROM jobs WHERE id=?", (jid,)).fetchone()
            emit("delivery", id=jid, generation=job["generation"], delivered=bool(job["delivered"]),
                 status=job["status"], outcome=json.loads(job["result"]).get("status"))
        return result

    Runtime._commit = committed
    for provider in discover():
        enable(args.data, provider.id, provider.version, provider.payload)
    app = create_app(ServerConfig(bundles=[args.bundle], data_dir=args.data,
        public_url=f"http://127.0.0.1:{args.port}", presenter_key="synthetic-load-key"))
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=args.port, log_level="warning"))
    def stop_on_stdin():
        if sys.stdin.readline().strip() == "stop":
            server.should_exit = True
    threading.Thread(target=stop_on_stdin, daemon=True).start()
    server.run()
    output.close()


if __name__ == "__main__":
    main()
