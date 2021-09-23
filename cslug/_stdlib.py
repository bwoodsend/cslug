# -*- coding: utf-8 -*-
"""
"""

import os
import ctypes.util
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

# POSIX should be really simple. The POSIX standard states that a libc, libm and
# libdl (names are not set in stone) should all be linkable via the names 'c',
# 'm' and 'dl' (names are set in stone) respectively. The symbols we're
# interested in a mostly in libc but with math symbols in libm and DLL related
# symbols in libdl. ctypes.util.find_library() should be able to convert linker
# names like 'c' to the OS's DLL name to be passed to ctypes.CDLL().
# In reality however:
#   - The POSIX standard isn't always followed.
#   - find_library() doesn't always work.
#   - libm and libdl are often either empty (with all their symbols moved to
#     libc) or are symlinks to libc.

elif OS == "Darwin":  # pragma: Darwin
    # On macOS >= 11.0, find_library() no longer works because system libraries
    # aren't physical files anymore but something more abstract. Fortunately,
    # you can just request libc directly. It contains all standard library
    # symbols.
    stdlib = ctypes.CDLL("libc.dylib")
    dlclose = stdlib.dlclose

elif OS.startswith("MSYS"):  # pragma: msys
    # On MSYS2, find_library() returns 'msys_2_0.dll' when we really want the
    # un-normalised name 'msys-2.0.dll' which contains all the symbols we want.
    # So this must be handled manually.
    stdlib = ctypes.CDLL("msys-2.0.dll")
    dlclose = stdlib.dlclose

elif os.name == "posix":  # pragma: no cover
    # Generic POSIX: This includes all flavours of Linux (even those using
    # alternative libc implementations like Alpine with musl), Cygwin, FreeBSD,
    # and hopefully serves as a sensible default for untested POSIX platforms.

    def _find_check_load_library(name, libc: ctypes.CDLL):
        """Find a library, check that its findable, check that it's not an alias
        of libc, then open it. Raise a tangible error message telling the user
        that it's not their fault and to report it if things go wrong.
        """
        # Get the full name of the library (e.g. convert 'c' to 'libc.so.7').
        full_name = ctypes.util.find_library(name)

        # If find_library() yielded nothing:
        if full_name is None:
            # This happens on musl based Linux only if gcc is not installed.
            # Assume that a symlink to the full name exists by adding the
            # standard prefix and suffix.
            full_name = f"lib{name}.so"

        # If this library turns out to just be an alias for libc:
        if libc and full_name == libc._name:
            # Then there's no point in opening it again.
            return

        # Open the library.
        try:
            return ctypes.CDLL(full_name)
        except OSError:
            # This is fatal only libc.
            if libc is not None:
                return libc
            # This can fail is, like with msys-2.0.dll, find_library() gave us
            # some incompatibly normalised name like msys_2_0.dll. This will
            # need another explicit case handling like MSYS2 gets above.
            raise OSError(f"Un-openable standard library {name} => {full_name}."
                          f" Please report this on cslug's issue tracker.")

    libc = _find_check_load_library("c", None)
    libm = _find_check_load_library("m", libc)
    libdl = _find_check_load_library("dl", libc)
    extra_libs = [i for i in (libm, libdl) if i]

    stdlib = libc
    dlclose = (libdl or libc).dlclose

else:  # pragma: no cover
    # Default to do nothing.
    dlclose = null_free_dll
