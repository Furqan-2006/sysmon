"""
sysmon_bridge.py — Python ↔ C Bridge via ctypes
Loads sysmon.so and maps C structs to Python objects.
"""
import ctypes
import ctypes.util
from pathlib import Path
from flask import current_app


# ── ctypes struct mirrors (must match sysmon.h exactly) ──────────────────────

class _CpuInfo(ctypes.Structure):
    _fields_ = [
        ("user",          ctypes.c_double),
        ("system",        ctypes.c_double),
        ("idle",          ctypes.c_double),
        ("usage_percent", ctypes.c_double),
    ]

class _MemInfo(ctypes.Structure):
    _fields_ = [
        ("total_kb",     ctypes.c_long),
        ("used_kb",      ctypes.c_long),
        ("free_kb",      ctypes.c_long),
        ("available_kb", ctypes.c_long),
        ("usage_percent",ctypes.c_double),
    ]

class _DiskInfo(ctypes.Structure):
    _fields_ = [
        ("total_kb",     ctypes.c_long),
        ("used_kb",      ctypes.c_long),
        ("free_kb",      ctypes.c_long),
        ("usage_percent",ctypes.c_double),
    ]

class _ProcessInfo(ctypes.Structure):
    _fields_ = [
        ("total",    ctypes.c_int),
        ("running",  ctypes.c_int),
        ("sleeping", ctypes.c_int),
    ]


# ── Loader ────────────────────────────────────────────────────────────────────

_lib = None

def _load_lib():
    global _lib
    if _lib is not None:
        return _lib

    lib_path = current_app.config["C_LIB_PATH"]
    if not Path(lib_path).exists():
        raise RuntimeError(
            f"C extension not found at {lib_path}. "
            "Run: cd c_extension && make"
        )

    _lib = ctypes.CDLL(lib_path)

    # Set return types
    _lib.get_cpu_info.restype     = _CpuInfo
    _lib.get_mem_info.restype     = _MemInfo
    _lib.get_disk_info.restype    = _DiskInfo
    _lib.get_process_info.restype = _ProcessInfo
    _lib.get_uptime_seconds.restype = ctypes.c_double

    return _lib


# ── Public API ────────────────────────────────────────────────────────────────

def get_cpu():
    raw = _load_lib().get_cpu_info()
    return {
        "usage_percent": round(raw.usage_percent, 2),
        "user":          round(raw.user, 2),
        "system":        round(raw.system, 2),
        "idle":          round(raw.idle, 2),
    }

def get_memory():
    raw = _load_lib().get_mem_info()
    KB  = 1024.0
    return {
        "total_mb":      round(raw.total_kb     / KB, 1),
        "used_mb":       round(raw.used_kb      / KB, 1),
        "free_mb":       round(raw.free_kb      / KB, 1),
        "available_mb":  round(raw.available_kb / KB, 1),
        "usage_percent": round(raw.usage_percent, 2),
    }

def get_disk():
    raw = _load_lib().get_disk_info()
    MB  = 1024.0 * 1024.0
    return {
        "total_gb":      round(raw.total_kb / MB, 2),
        "used_gb":       round(raw.used_kb  / MB, 2),
        "free_gb":       round(raw.free_kb  / MB, 2),
        "usage_percent": round(raw.usage_percent, 2),
    }

def get_processes():
    raw = _load_lib().get_process_info()
    return {
        "total":    raw.total,
        "running":  raw.running,
        "sleeping": raw.sleeping,
    }

def get_uptime():
    secs = _load_lib().get_uptime_seconds()
    h, rem = divmod(int(secs), 3600)
    m, s   = divmod(rem, 60)
    return {
        "seconds": round(secs, 1),
        "formatted": f"{h}h {m}m {s}s",
    }

def get_all_metrics():
    """Collect all metrics in one call (used by snapshot recorder)."""
    return {
        "cpu":       get_cpu(),
        "memory":    get_memory(),
        "disk":      get_disk(),
        "processes": get_processes(),
        "uptime":    get_uptime(),
    }
