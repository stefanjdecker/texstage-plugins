# SPDX-License-Identifier: Apache-2.0
"""Read-only timing instrumentation around the ordinary disposable FD server.

Does not alter leases, queue policy, worker limits or provider behavior. Logs
synthetic IDs, sizes and timings only; never answer data or authentication tokens.
"""
import ctypes
import json
import os
from pathlib import Path
import runpy
import sys
import time

from texstage.plugins.runtime import Runtime
from texstage.server.app import Server

data = Path(sys.argv[sys.argv.index('--data') + 1])
data.mkdir(parents=True, exist_ok=True)
stream = (data / 'classroom-events.jsonl').open('w', encoding='utf-8', buffering=1)
submissions = 0
finish_calls = 0
if os.environ.get('TEXSTAGE_CLASSROOM_PROFILE') == 'finish':
    import cProfile
    finish_profile = cProfile.Profile()
else:
    finish_profile = None


def rss():
    if os.name != 'nt':
        return None
    class Counters(ctypes.Structure):
        _fields_ = [('cb', ctypes.c_ulong), ('PageFaultCount', ctypes.c_ulong)] + [
            (name, ctypes.c_size_t) for name in ('PeakWorkingSetSize', 'WorkingSetSize',
            'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
            'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
    c = Counters()
    c.cb = ctypes.sizeof(c)
    kernel = ctypes.windll.kernel32
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    fn = ctypes.windll.psapi.GetProcessMemoryInfo
    fn.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
    return c.WorkingSetSize if fn(kernel.GetCurrentProcess(), ctypes.byref(c), c.cb) else None


def emit(event, **fields):
    stream.write(json.dumps({'event': event, 'ms': time.perf_counter() * 1000,
                             'rss_bytes': rss(), **fields}, separators=(',', ':')) + '\n')


def instrument(name):
    original = getattr(Runtime, name)
    def call(self, *args, **kwargs):
        global submissions, finish_calls
        start = time.perf_counter()
        if name == 'finish': finish_calls += 1
        if name == 'finish' and finish_profile is not None and 20 < finish_calls <= 120:
            result = finish_profile.runcall(original, self, *args, **kwargs)
            if finish_calls == 120: finish_profile.dump_stats(str(data / 'classroom-finish.prof'))
        else:
            result = original(self, *args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        if name == 'command':
            command = args[3]
            if command['operation'] == 'submit':
                submissions += 1
            emit('command', operation=command['operation'], request=command['request_id'],
                 item=command['item'], receipt=result, duration_ms=elapsed)
        elif name == 'lease' and result:
            emit('lease', jobs=[{k: j[k] for k in ('id', 'generation', 'epoch')} for j in result],
                 duration_ms=elapsed)
        elif name == 'finish':
            emit('finish', job=args[2]['id'], generation=args[2]['generation'], accepted=result,
                 status=args[2]['outcome']['status'], duration_ms=elapsed,
                 state_bytes=max((len(r[0].encode('utf-8')) for r in self.db.execute('SELECT state FROM items')), default=0))
        return result
    setattr(Runtime, name, call)


for name in ('command', 'lease', 'finish'):
    instrument(name)
if os.environ.get('TEXSTAGE_CLASSROOM_PROFILE') == '1':
    import cProfile
    original_push = Server.push
    def profiled_push(self, *args, **kwargs):
        if submissions >= 64 and not (data / 'classroom-push.prof').exists():
            profiler = cProfile.Profile()
            result = profiler.runcall(original_push, self, *args, **kwargs)
            profiler.dump_stats(str(data / 'classroom-push.prof'))
            return result
        return original_push(self, *args, **kwargs)
    Server.push = profiled_push
emit('start', pid=os.getpid())
runpy.run_path(str(Path(__file__).with_name('serve_fd_lesson.py')), run_name='__main__')
