import os
import shutil
from pathlib import Path
import re
from subprocess import run, PIPE
import platform

from cslug import exceptions


def which(name):
    """Locate an executable in ``PATH``.

    This is equivalent to `shutil.which` except that if you give it a path
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

    if platform.system() in ("Darwin", "FreeBSD",
                             "OpenBSD"):  # pragma: no cover
        # These platforms officially use clang as their default compilers.
        CC = which("clang") or which("gcc")
    else:
        CC = which("gcc")  # pragma: no cover
    if CC is None:  # pragma: no branch
        raise exceptions.NoGccError
    return CC  # pragma: no cover


def cc_version(CC=None):
    """Get C compiler's name and version.

    Args:
        CC: See `cslug.cc`.

    Returns:
        (str, tuple[int]): A ``(name, version_info)`` pair.

    The ``name`` is determined by parsing the output of ``$CC -v`` (or
    ``%CC% -v`` on Windows). It can be:

    - ``'gcc'`` for `gcc`_ (both 32 and 64 bit).
    - ``'tcc'`` for `TinyCC`_ including the 32-bit ``i386-win32-tcc`` version.
    - ``'clang'`` for clang_.
    - ``'pcc'`` for `Portable C Compiler`_.
    - ``'PGCC'`` for pgcc_.

    The ``version_info`` is in the standard ``(major, minor, micro)`` version
    format.

    """
    CC = cc(CC)
    # This function is split into two so that both ``$CC -v`` and
    # ``$CC --version`` can be tried.
    try:
        return _cc_version(CC, "-v")
    except RuntimeError:  # pragma: no cover
        # Currently, the only compiler to need this variant is pgcc.
        return _cc_version(CC, "--version")


def _cc_version(*command):
    """Execute some form of ``$CC --what-are-you`` command and attempt to parse
    the output."""
    p = run(command, stdout=PIPE, stderr=PIPE)

    # Some compilers use stdout and others use stderr - combine them.
    stdout = p.stdout + p.stderr

    return _parse_cc_version(stdout, p.args)


def _parse_cc_version(stdout: bytes, cmd: list):
    """The parser for `cc_version`.

    Args:
        stdout:
            Whatever ``$CC -v`` gives.
        cmd:
            The command used to obtain **stdout**. Only needed to display in
            case of an error.
    Returns:
        (str, tuple[int]): A ``(name, version_info)`` pair.

    """
    # Most compilers (namely gcc, clang and tcc) use the format
    # "[name] version [version]" but pcc and pgcc have their own..
    m = re.search(rb"(\S+) version ([\d.]+)", stdout) \
        or re.search(rb"(pcc) ([\d.]+) for \S+", stdout) \
        or re.search(rb"(pgcc) \D* ([\d.]+)", stdout)

    try:
        name, version = m.groups()
        return name.decode(), tuple(map(int, version.split(b".")))
    except:
        from textwrap import indent
        raise RuntimeError(
            f"Failed to get CC version from the output of\n    {cmd}\n::\n"
            f"{indent(stdout.decode(errors='replace'), '    ')}") from None


def mmacosx_version_min():  # pragma: Darwin
    """Get a value to be used for the ``-mmacosx-version-min`` compiler option.
    """

    # The default value should be kept in sync with the minimum macOS version
    # compiled against on https://www.python.org/downloads/mac-osx/ for the
    # oldest Python version supported by cslug so as to
    # maximise -mmacosx-version-min without cutting off anything that Python
    # doesn't already. Whilst cslug supports:
    # - Python 3.8-3.11 -> OSX 10.9
    default = "10.9"

    target = os.environ.get("MACOSX_DEPLOYMENT_TARGET") or \
             os.environ.get("MACOS_DEPLOYMENT_TARGET") or  default
    if (macos_architecture() or platform.machine()) == "arm64":
        # arm64 only wheels must be declared >= 11.0 compatible or they are not
        # deemed installable. A universal2 wheel does not have this constraint.
        if float(target) < 11:
            target = "11.0"
    if "." not in target:
        target += ".0"
    return target


def macos_architecture():  # pragma: Darwin
    """Read and validate the contents of the `MACOS(X)_ARCHITECTURE`
    environment variable.

    Returns:
        One of :py:`('x86_64', 'arm64', 'universal2', None)`.
    Raises:
        EnvironmentError:
            If its value is not one of the above.

    """
    if platform.system() == "Darwin":  # pragma: no branch
        return _macos_architecture(
            os.environ.get("MACOSX_ARCHITECTURE")
            or os.environ.get("MACOS_ARCHITECTURE"))


def _macos_architecture(env_value):
    """The platform and environment independent logic behind
    macos_architecture().
    """
    if not env_value:
        return
    valid = ("arm64", "x86_64", "universal2")
    if env_value in valid:
        return env_value
    elif sorted(re.findall(r"[^\s,]+", env_value)) == ["arm64", "x86_64"]:
        return "universal2"
    raise EnvironmentError(f"The MACOSX_ARCHITECTURE environment variable must "
                           f"be one of {valid}. Received '{env_value}'.")
