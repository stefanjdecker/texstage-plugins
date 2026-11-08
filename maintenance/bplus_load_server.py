# SPDX-License-Identifier: Apache-2.0
"""Loopback classroom probe. Observe real hooks, durable jobs and broadcasts.

Instrumentation changes no limits, authentication, evaluator policy or deadlines.
Only timings, synthetic request IDs and aggregate counts are written to metrics.
"""
import argparse
import json
import sys
import threading
import time
from pathlib import Path

import uvicorn
from texstage.plugins.catalog import discover
from texstage.plugins.policy import enable
from texstage.plugins.runtime import Runtime
from texstage.plugins.worker import Workers
from texstage.server.app import Server, ServerConfig, create_app
from texstage.server.plugins import PluginHost


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("bundle", "data", "metrics"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    args.metrics.parent.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    with args.metrics.open("w", encoding="utf-8", buffering=1, newline="\n") as output:
        def emit(kind, **fields):
            output.write(json.dumps({"event": kind, "ms": (time.perf_counter() - start) * 1000, **fields}) + "\n")

        hook = Workers.call
        def measured_hook(self, cid, method, *values):
            before, error = time.perf_counter(), None
            try:
                return hook(self, cid, method, *values)
            except Exception as exc:
                error = type(exc).__name__
                raise
            finally:
                emit("hook", method=method, duration_ms=(time.perf_counter() - before) * 1000, error=error)
        Workers.call = measured_hook
        views = Workers.views
        def measured_views(self, cid, state, audiences, ctx):
            before, error = time.perf_counter(), None
            try:
                return views(self, cid, state, audiences, ctx)
            except Exception as exc:
                error = type(exc).__name__
                raise
            finally:
                emit("hook", method="view_batch", count=len(audiences),
                     duration_ms=(time.perf_counter() - before) * 1000, error=error)
        Workers.views = measured_views
        for method in ("command", "lease", "finish"):
            original = getattr(Runtime, method)
            def measured(self, *values, _method=method, _original=original, **kwargs):
                before = time.perf_counter()
                result = _original(self, *values, **kwargs)
                fields = {"duration_ms": (time.perf_counter() - before) * 1000}
                if _method == "command":
                    fields.update(operation=values[3]["operation"], request=values[3]["request_id"], receipt=result)
                elif _method == "lease":
                    fields["jobs"] = [{k: job[k] for k in ("id", "generation")} for job in result]
                else:
                    fields.update(id=values[2]["id"], generation=values[2]["generation"],
                                  outcome=values[2]["outcome"]["status"], accepted=result)
                emit(_method, **fields)
                return result
            setattr(Runtime, method, measured)
        push = Server.push
        def measured_push(self, *values, **kwargs):
            before = time.perf_counter()
            result = push(self, *values, **kwargs)
            emit("broadcast", duration_ms=(time.perf_counter() - before) * 1000)
            return result
        Server.push = measured_push
        disconnect = PluginHost.disconnect
        def measured_disconnect(self, conn):
            if conn.role == "stage": emit("evaluator-disconnect")
            return disconnect(self, conn)
        PluginHost.disconnect = measured_disconnect
        for provider in discover():
            enable(args.data, provider.id, provider.version, provider.payload)
        app = create_app(ServerConfig(bundles=[args.bundle], data_dir=args.data,
            public_url=f"http://127.0.0.1:{args.port}", presenter_key="synthetic-load-key"))
        from webkit_http_diagnostics import wrap_http_diagnostics
        app = wrap_http_diagnostics(app, emit)
        server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=args.port, log_level="warning"))
        def stop():
            if sys.stdin.readline().strip() == "stop": server.should_exit = True
        threading.Thread(target=stop, daemon=True).start()
        server.run()


if __name__ == "__main__":
    main()
