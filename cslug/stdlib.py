# -*- coding: utf-8 -*-
r"""
Standard library C functions exposed to Python.

Most of the functions in the C standard library are included in a single |shared
library| which is part of your operating system (see the table below). The
:mod:`cslug.stdlib` module loads and exposes the contents of this library to be
directly called from Python.

========  ==========================================================================
Platform  Library/location
========  ==========================================================================
Linux     A combination of ``libc.so`` and, if present and not just aliases of ``libc.so``, ``libm.so`` and ``libdl.so``.
Windows   The somewhat barren ``C:\Windows\system32\msvcrt.dll``.
macOS     ``libc.dylib``.
MSYS2     ``msys-2.0.dll``, requires ``cslug >= 0.5.1`` for newer versions of Python.
Cygwin    ``cygwin1.dll``, requires ``cslug >= 0.4.0``.
FreeBSD   A combination of ``libc.so`` and ``libm.so``.
Android   A combination of ``libc.so`` and ``libm.so``.
========  ==========================================================================


Not every function is made available. A function is excluded if:

* It is not available on every supported platform (shoots a filthy look towards
  Windows) so that you don't have to worry about cross-platform compatibility.
* It uses types which are unavailable to :mod:`ctypes`.
* It's a macro, meaning that it's refactored away at compile time and doesn't
  exist in any |binaries| format.


.. note::

    These functions are tested to check that they exist but not that they work
    in Python. I don't even know what half of them do...

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
