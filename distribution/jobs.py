"""Encadre le moteur Windows par un Job Object pour libérer ses descendants."""

import os
from contextlib import contextmanager


class ChildJob:
    def __init__(self):
        self.handle = None

    def assign(self, process):
        if os.name != "nt":
            return
        import ctypes as c
        from ctypes import wintypes as w

        class BasicLimits(c.Structure):
            _fields_ = [("process_time", c.c_int64), ("job_time", c.c_int64), ("flags", w.DWORD),
                        ("min_ws", c.c_size_t), ("max_ws", c.c_size_t), ("processes", w.DWORD),
                        ("affinity", c.c_size_t), ("priority", w.DWORD), ("schedule", w.DWORD)]

        class ExtendedLimits(c.Structure):
            _fields_ = [("basic", BasicLimits), ("io_counters", c.c_uint64 * 6),
                        ("process_memory", c.c_size_t), ("job_memory", c.c_size_t),
                        ("peak_process", c.c_size_t), ("peak_job", c.c_size_t)]

        kernel = c.WinDLL("kernel32", use_last_error=True)
        kernel.CreateJobObjectW.argtypes = (c.c_void_p, w.LPCWSTR)
        kernel.CreateJobObjectW.restype = w.HANDLE
        kernel.SetInformationJobObject.argtypes = (w.HANDLE, c.c_int, c.c_void_p, w.DWORD)
        kernel.AssignProcessToJobObject.argtypes = (w.HANDLE, w.HANDLE)
        kernel.CloseHandle.argtypes = (w.HANDLE,)
        kernel.OpenProcess.argtypes = (w.DWORD, w.BOOL, w.DWORD)
        kernel.OpenProcess.restype = w.HANDLE

        self.handle = kernel.CreateJobObjectW(None, None)
        self.close_handle = kernel.CloseHandle
        if not self.handle:
            raise c.WinError(c.get_last_error())
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        child = kernel.OpenProcess(0x101, False, process.pid)  # TERMINATE | SET_QUOTA
        try:
            if (not child or not kernel.SetInformationJobObject(self.handle, 9, c.byref(limits), c.sizeof(limits))
                    or not kernel.AssignProcessToJobObject(self.handle, child)):
                raise c.WinError(c.get_last_error())
        except OSError:
            self.close()
            raise
        finally:
            if child:
                kernel.CloseHandle(child)

    def close(self):
        if self.handle:
            self.close_handle(self.handle)
            self.handle = None


@contextmanager
def stop_waiter(pid):
    """Ouvrir le processus authentifié avant l’arrêt et attendre sa sortie sur Windows."""
    if os.name != "nt":
        yield lambda _seconds: None
        return
    import ctypes as c
    from ctypes import wintypes as w

    kernel = c.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = (w.DWORD, w.BOOL, w.DWORD)
    kernel.OpenProcess.restype = w.HANDLE
    kernel.WaitForSingleObject.argtypes = (w.HANDLE, w.DWORD)
    kernel.WaitForSingleObject.restype = w.DWORD
    kernel.CloseHandle.argtypes = (w.HANDLE,)
    handle = kernel.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE uniquement
    if not handle:
        raise c.WinError(c.get_last_error())

    def wait(seconds):
        outcome = kernel.WaitForSingleObject(handle, max(0, int(seconds * 1000)))
        if outcome == 258:  # WAIT_TIMEOUT
            raise ValueError("Windows n’a pas confirmé la sortie du serveur dans le délai prévu.")
        if outcome != 0:
            raise c.WinError(c.get_last_error())

    try:
        yield wait
    finally:
        kernel.CloseHandle(handle)
