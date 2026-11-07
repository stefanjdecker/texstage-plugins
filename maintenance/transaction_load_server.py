# SPDX-License-Identifier: Apache-2.0
"""Reuse the bounded host probe and record the server's OS peak resident memory."""
import argparse
import json
import sys
import threading
from pathlib import Path
from bplus_load_server import main


def peak_rss():
    if sys.platform == 'win32':
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [('cb',wintypes.DWORD),('faults',wintypes.DWORD)] + [
                (name,ctypes.c_size_t) for name in ('peak','working','peak_paged','paged','peak_nonpaged','nonpaged','pagefile','peak_pagefile')]
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.GetCurrentProcess.restype=wintypes.HANDLE
        memory=ctypes.WinDLL('psapi',use_last_error=True).GetProcessMemoryInfo
        memory.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
        memory.restype=wintypes.BOOL
        counters=Counters();counters.cb=ctypes.sizeof(counters)
        if not memory(kernel.GetCurrentProcess(),ctypes.byref(counters),counters.cb):
            return None
        return counters.peak
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)


if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--metrics',type=Path,required=True)
    args,_=parser.parse_known_args()
    # Keep memory separate from the shared event stream. A forced shutdown must
    # still leave the latest sample; it must not masquerade as a measured zero.
    memory_path = args.metrics.with_suffix('.memory.json')
    stop = threading.Event()
    def sample():
        while not stop.is_set():
            value = {'server_peak_rss_bytes': peak_rss()}
            temporary = memory_path.with_suffix('.tmp')
            temporary.write_text(json.dumps(value)+'\n', encoding='utf-8')
            temporary.replace(memory_path)
            stop.wait(1)
    sampler = threading.Thread(target=sample, daemon=True)
    sampler.start()
    try:
        main()
    finally:
        stop.set()
        sampler.join(timeout=2)
