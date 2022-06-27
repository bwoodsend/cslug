# -*- coding: utf-8 -*-
r"""
Standard library C functions exposed to Python.

Most of the functions in the C standard library are included in a single
|shared library| which is part of your operating system (see the table below).
The `cslug.stdlib` module loads and exposes the contents of this library to be
directly called from Python.

============  ==========================================================================
Platform      Library/location
============  ==========================================================================
Linux          A combination of ``libc.so`` and, if present and not just aliases of ``libc.so``, ``libm.so`` and ``libdl.so``.
Windows >11   ``C:\Windows\system32\ucrt.dll``
Windows 7-10  The somewhat barren ``C:\Windows\system32\msvcrt.dll``.
macOS         ``libc.dylib``.
MSYS2         ``msys-2.0.dll``, requires ``cslug >= 0.5.1`` for newer versions of Python.
Cygwin        ``cygwin1.dll``, requires ``cslug >= 0.4.0``.
FreeBSD       A combination of ``libc.so`` and ``libm.so``.
OpenBSD       A combination of ``libc.so`` and ``libm.so``.
Android       A combination of ``libc.so`` and ``libm.so``.
============  ==========================================================================


Not every function is made available. A function is excluded if:

* It is not available on your current platform.
* It uses types which are unavailable to `ctypes`.
* It's a macro, meaning that it's refactored away at compile time and doesn't
  exist in any |binaries| format.

"""


def _init():
    import io
    from pathlib import Path
    from cslug import __loader__, Types
    from cslug._stdlib import stdlib, extra_libs
    json = Path(__file__).with_suffix(".json")

    _std_types = Types(io.StringIO(__loader__.get_data(str(json)).decode()))
    _std_types.init_from_json()

    globals().update(_std_types._merge_apply(stdlib, *extra_libs))
    __all__ = list(_std_types.functions)

    return _std_types, __all__


_std_types, __all__ = _init()
