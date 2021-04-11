# -*- coding: utf-8 -*-
"""
"""

import os, sys
import ctypes
import platform

OS = platform.system()


def null_free_dll(*spam):  # pragma: no cover
    pass


# Try to find a good runtime library which is always available and contains
# the standard library C functions such as malloc() or printf().
# XXX: Keep chosen library names in sync with the table in `cslug/stdlib.py`.

extra_libs = []

if OS == "Windows":  # pragma: Windows
    _dlclose = ctypes.windll.kernel32.FreeLibrary
    dlclose = lambda handle: 0 if _dlclose(handle) else 1
    # There's some controversy as to whether this DLL is guaranteed to exist.
    # It always has so far but isn't documented. However, MinGW assumes that it
    # is so, should this DLL be removed, then we have much bigger problems than
    # just this line. There is also vcruntime140.dll which isn't a standard part
    # of the OS but is always shipped with Python so we can guarantee its
    # presence. But vcruntime140 contains only a tiny strict-subset of msvcrt.
    stdlib = ctypes.CDLL("msvcrt")

elif OS == "Darwin":  # pragma: Darwin
    try:
        try:
            # macOS 11 (Big Sur). Possibly also later macOS 10s.
            stdlib = ctypes.CDLL("libc.dylib")
        except OSError:  # pragma: no cover
            stdlib = ctypes.CDLL("libSystem")
    except OSError:  # pragma: no cover
        # Older macOSs. Not only is the name inconsistent but it's
        # not even in PATH.
        _stdlib = "/usr/lib/system/libsystem_c.dylib"
        if os.path.exists(_stdlib):
            stdlib = ctypes.CDLL(_stdlib)
        else:
            stdlib = None
    if stdlib is not None:  # pragma: no branch
        dlclose = stdlib.dlclose
    else:  # pragma: no cover
        # I hope this never happens.
        dlclose = null_free_dll

elif OS == "Linux":  # pragma: Linux
    try:
        stdlib = ctypes.CDLL("")
    except OSError:  # pragma: no cover
        # Either Alpine Linux or Android.
        # Unfortunately, there doesn't seem to be any practical way
        # to tell them apart.
        stdlib = ctypes.CDLL("libc.so")

        # Android, like FreeBSD puts its math functions
        # in a dedicated `libm.so`.
        # The only way to know that this is not Alpine is to check if the math
        # functions are already available in `libc.so`.
        if not hasattr(stdlib, "sin"):
            extra_libs.append(ctypes.CDLL("libm.so"))
    dlclose = stdlib.dlclose

elif sys.platform == "msys":  # pragma: msys
    # msys can also use `ctypes.CDLL("kernel32.dll").FreeLibrary()`. Not sure
    # if or what the difference is.
    stdlib = ctypes.CDLL("msys-2.0.dll")
    dlclose = stdlib.dlclose

elif sys.platform == "cygwin":  # pragma: cygwin
    stdlib = ctypes.CDLL("cygwin1.dll")
    dlclose = stdlib.dlclose

elif OS == "FreeBSD":  # pragma: FreeBSD
    # FreeBSD uses `/usr/lib/libc.so.7` where `7` is anothoer version number.
    # It is not in PATH but using its name instead of its path is somehow the
    # only way to open it. The name must include the .so.7 suffix.
    stdlib = ctypes.CDLL("libc.so.7")
    dlclose = stdlib.close
    # Maths functions are in a separate library.
    extra_libs.append(ctypes.CDLL("libm.so.5"))

else:  # pragma: no cover
    # Default to do nothing.
    dlclose = null_free_dll
