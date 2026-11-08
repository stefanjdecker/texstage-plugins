# SPDX-License-Identifier: Apache-2.0
"""Bounded Linux crash diagnostics around the unchanged synthetic load probes.

Only use synthetic example bundles. This records owned process metadata and
native backtraces, never process environments or real classroom submissions.
It does not alter browser flags, worker policy, deadlines, or load-test gates.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import time


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def sample(root_pid: int, known: dict[str, str]) -> dict:
    rows = {}
    for directory in Path("/proc").glob("[0-9]*"):
        try:
            status = dict(line.split(":", 1) for line in (directory / "status").read_text().splitlines())
            rows[int(directory.name)] = {key: status.get(key, "").strip() for key in
                ("Name", "Pid", "PPid", "Threads", "VmRSS", "VmHWM", "VmSize")}
        except (OSError, ValueError):
            pass
    owned = {root_pid}
    while True:
        children = {pid for pid, row in rows.items() if int(row["PPid"]) in owned}
        if children <= owned:
            break
        owned |= children
    result = []
    for pid in sorted(owned):
        if pid not in rows:
            continue
        row = rows[pid]
        try:
            row["fds"] = len(list(Path(f"/proc/{pid}/fd").iterdir()))
            row["executable"] = os.readlink(f"/proc/{pid}/exe")
            known[str(pid)] = row["executable"]
        except OSError:
            pass
        result.append(row)
    system = {}
    for name in ("MemAvailable", "MemFree", "SwapFree"):
        match = re.search(rf"^{name}:\s*(.+)$", Path("/proc/meminfo").read_text(), re.M)
        if match:
            system[name] = match[1]
    cgroup = {}
    for name in ("memory.current", "memory.peak", "memory.events", "pids.current", "pids.peak", "pids.max"):
        path = Path("/sys/fs/cgroup") / name
        if path.exists():
            cgroup[name] = path.read_text().strip()
    return {"processes": result, "system": system, "cgroup": cgroup}


def backtraces(cores: Path | None, output: Path, known: dict[str, str]) -> list[str]:
    captured = []
    if not cores:
        return captured
    for core in sorted(cores.glob("core.*.*")):
        # CI uses core.%e.%p. Only inspect processes observed as our descendants.
        executable = known.get(core.name.rsplit(".", 1)[-1])
        if not executable:
            continue
        target = output / (core.name + ".gdb.log")
        args = ["gdb", "--batch", "--quiet", "-iex", "set auto-load off",
                "-ex", "set pagination off", "-ex", "info files",
                "-ex", "info sharedlibrary", "-ex", "bt 40",
                "-ex", "info registers", "-ex", "x/12i $pc-16",
                "-ex", "thread apply all bt 12", executable, str(core)]
        try:
            with target.open("w") as log:
                subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, timeout=120,
                               env=os.environ | {"DEBUGINFOD_URLS": ""}, check=False)
            captured.append(target.name)
        except (OSError, subprocess.TimeoutExpired) as error:
            target.write_text(target.read_text() + f"\nDebugger failure: {error}\n")
    return captured


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=["transaction", "bplus"])
    parser.add_argument("bundle", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--actors", type=int, choices=[600, 1000], required=True)
    parser.add_argument("--cores", type=Path)
    args = parser.parse_args()
    if platform.system() != "Linux":
        parser.error("Native process diagnostics require Linux")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    known: dict[str, str] = {}
    env = os.environ | {"DEBUG": "pw:browser", "BROWSER": "webkit",
                       f"{args.kind.upper()}_ACTORS": str(args.actors),
                       "TRANSACTION_WAVE_SECONDS": "0"}
    script = Path(__file__).with_name(f"{args.kind}_load_browser.cjs")
    command = ["node", str(script), str(args.bundle.resolve()), str(output / "load")]
    timed_out = False
    with (output / "browser.log").open("w") as log, (output / "processes.jsonl").open("w") as metrics:
        process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        while process.poll() is None:
            metrics.write(json.dumps({"seconds": round(time.monotonic() - started, 3),
                                      **sample(process.pid, known)}) + "\n")
            metrics.flush()
            if time.monotonic() - started >= 600:
                timed_out = True
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                break
            time.sleep(0.5)
        metrics.write(json.dumps({"seconds": round(time.monotonic() - started, 3),
                                  **sample(process.pid, known)}) + "\n")
    code = process.wait()
    write_json(output / "executables.json", known)
    traces = backtraces(args.cores, output, known)
    report = {"kind": args.kind, "actors": args.actors, "exit_code": code,
              "timed_out": timed_out, "seconds": round(time.monotonic() - started, 3),
              "platform": platform.platform(), "python": platform.python_version(),
              "node": subprocess.check_output(["node", "--version"], text=True).strip(),
              "backtraces": traces, "load_report": "load/report.json"}
    write_json(output / "diagnostic.json", report)
    print(json.dumps(report), flush=True)
    # Do not turn a failed original correctness/performance gate into success.
    return 124 if timed_out else code if code >= 0 else 128 - code


if __name__ == "__main__":
    raise SystemExit(main())
