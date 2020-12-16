# -*- coding: utf-8 -*-
"""
"""

import os, sys
import ctypes
import platform

OS = platform.system()


def null_free_dll(*spam):  # pragma: no cover
    pass


if OS == "Windows":  # pragma: Windows
    _dlclose = ctypes.windll.kernel32.FreeLibrary
    dlclose = lambda handle: 0 if _dlclose(handle) else 1

elif OS == "Darwin":  # pragma: Darwin
    try:
        stdlib = ctypes.CDLL("libSystem")
    except OSError:
        # Older macOSs. Not only is the name inconsistent but it's
        # not even in PATH.
        _stdlib = "/usr/lib/system/libsystem_c.dylib"
        if os.path.exists(_stdlib):
            stdlib = ctypes.CDLL(_stdlib)
        else:
            stdlib = None
    if stdlib is not None:
        dlclose = stdlib.dlclose
    else:
        # I hope this never happens.
        dlclose = null_free_dll

elif OS == "Linux":  # pragma: Linux
    stdlib = ctypes.CDLL("")
    dlclose = stdlib.dlclose

elif sys.platform == "msys":  # pragma: msys
    # msys can also use `ctypes.CDLL("kernel32.dll").FreeLibrary()`. Not sure
    # if or what the difference is.
    stdlib = ctypes.CDLL("msys-2.0.dll")
    dlclose = stdlib.dlclose

else:  # pragma: no cover
    # Default to do nothing.
    dlclose = null_free_dll