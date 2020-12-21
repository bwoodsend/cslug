# -*- coding: utf-8 -*-
"""
"""

import os
import shutil
from pathlib import Path
import re
from subprocess import run, PIPE

from cslug import exceptions


def which(name):
    """Locate an executable in ``PATH``.

    This is equivalent to :func:`shutil.which` except that if you give it a path
    instead of just a name, it returns that path. The output of this function
    will always include the executable suffix.

    """
    if not os.path.dirname(name):
        return shutil.which(name)
    path = Path(name)

    if path.is_file():
        return name

    # Ensure /path/to/executable is expanded to /path/to/executable.exe or any
    # suffix in ``PATHEXT`` on Windows.
    return shutil.which(path.name, path=str(path.parent))


def cc(CC=None):
    """Get the full path of the C compiler.

    Args:
        CC: Value to override the **CC** environment variable.

    Returns:
        str: Full path of the C compiler.

    Raises:
        exceptions.NoGccError: If **CC** is unset and |gcc| was not found in
            ``PATH``.
        exceptions.CCNotFoundError: If **CC** is set but couldn't be found.
        exceptions.BuildBlockedError: If **CC** is set to ``!block``.

    The C compiler is chosen by the **CC** environment variable.

    * If **CC** is unset then it defaults to ``gcc``.
    * If **CC** is a name, such as ``gcc`` or ``clang``, then it is searched for
      in ``PATH`` (respecting ``PATHEXT`` on Windows).
    * If **CC** is a relative path, such as ``./gcc``, then it is made absolute.
    * If **CC** is an absolute path then it is returned as is.
    * If **CC** is ``!block`` then an error is raised. This can be used to test
      your pre-built package works without a compiler.

    .. note:: The value of **CC** should never be wrapped in quotes.

    """
    CC = CC or os.environ.get("CC", "").strip()
    if CC == "!block":
        raise exceptions.BuildBlockedError

    if CC:
        _cc = which(CC)
        if _cc is None:
            raise exceptions.CCNotFoundError(CC)
        return _cc

    CC = which("gcc")
    if CC is None:
        raise exceptions.NoGccError
    return CC


def cc_version(CC=None):
    """Get C compiler's name and version.

    Args:
        CC: See :func:`cslug.cc`.

    Returns:
        (str, tuple[int]): A ``(name, version_info)`` pair.

    The `name` is determined by parsing the output of ``$CC -v`` (or ``%CC% -v``
    on Windows). It can be:

    - ``'gcc'`` for `gcc`_ (both 32 and 64 bit).
    - ``'tcc'`` for `TinyCC`_ including the 32-bit ``i386-win32-tcc`` version.
    - ``'clang'`` for clang_.
    - ``'pcc'`` for `Portable C Compiler`_.

    The `version_info` is in the standard ``(major, minor, micro)`` version
    format.

    """
    cmd = [cc(CC), "-v"]
    p = run(cmd, stdout=PIPE, stderr=PIPE)

    # Some compilers use stdout and others use stderr - combine them.
    stdout = p.stdout + p.stderr
    # All compilers except pcc use the format "[name] version [version]".
    m = re.search(rb"(\S+) version (\S+)", stdout) \
        or re.search(rb"(pcc) (\S+) for \S+", stdout)

    try:
        name, version = m.groups()
        return name.decode(), tuple(map(int, version.split(b".")))
    except:  # pragma: no cover
        from textwrap import indent
        raise RuntimeError(
            f"Failed to get CC version from the output of\n    {cmd}\n::\n"
            f"{indent(stdout.decode(errors='replace'), '    ')}") from None
