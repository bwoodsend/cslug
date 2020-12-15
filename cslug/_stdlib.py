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
    dlclose = ctypes.windll.kernel32.FreeLibrary

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

else:  # pragma: no cover
    # XXX: This is for msys2. PR wanted from anyone who knows how to unload a
    #      DLL under such an environment.
    dlclose = null_free_dll
