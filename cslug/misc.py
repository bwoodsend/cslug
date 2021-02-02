# -*- coding: utf-8 -*-
"""
=================
:mod:`cslug.misc`
=================

The miff-muffet-moof module.

"""

import io as _io
import sys as _sys
import re as _re
from pathlib import Path as _Path
import contextlib as _contextlib
import functools as _funtiontools
import ctypes as _ctypes


def as_path_or_buffer(file):
    """Normalise filenames to :class:`pathlib.Path`, leaving streams untouched.
    """
    return file if isinstance(file, _io.IOBase) else _Path(file)


def as_path_or_readable_buffer(file):
    """Normalise filenames to :class:`pathlib.Path`, and streams to
    :class:`io.StringIO`.

    Streams need to be re-readable in |cslug|. An :class:`io.StringIO` is via
    ``file.getvalue()`` - everything else generally isn't. The goal of using
    :mod:`io` streams is only to prevent strings of source code from being
    confused for string filenames - not, as is the more normal usage, to avoid
    holding large files in memory.

    """
    if isinstance(file, _io.TextIOBase):
        if hasattr(file, "getvalue"):
            return file
        return _io.StringIO(file.read())
    return _Path(file)


def _read(path, mode="r"):
    if isinstance(path, _io.IOBase):
        if hasattr(path, "getvalue"):
            return path.getvalue(), None
        return path.read(), None
    with open(path, mode, encoding="utf-8") as f:
        return f.read(), path


def read(path, mode="r"):
    r"""Read a path or a stream.

    Line endings are normalised to Unix ``'\n'`` if :py:`mode == 'r'` so as to
    be consistent with :func:`open`.

    """
    text, path = _read(path, mode)
    if mode == "r":
        text = _re.sub("\r\n?", "\n", text)
    return text, path


def write(path, *data, mode="w"):
    """Write to a path or a stream.

    Args:
        path (str or os.PathLike or io.IOBase):
            File to write to.
        *data (str or bytes):
            Data to write.
        mode (str):
            A mode to be passed to :func:`open`, ignored if **path** is a
            stream.

    Returns:
        int: The number of characters written.

    If **path** is a stream it is simply written to without closing it
    afterwards. If **path** is a filename then it is opened, written to, then
    closed.

    """
    if isinstance(path, _io.IOBase):
        return path.writelines(data)
    with open(path, mode, encoding="utf-8") as f:
        return f.writelines(data)


def anchor(*paths):
    """Replace relative paths with frozen paths relative to ``__file__``\\ 's
    parent.

    :param paths: Path(s) to freeze or pseudo files.
    :type paths: str or os.PathLike or io.IOBase
    :return: List of modified paths.
    :rtype: list

    Pseudo files (:class:`io.IOBase`) and absolute paths are left unchanged. Use
    this function to make your code working-dir independent.
    """
    paths = map(as_path_or_buffer, paths)
    file = _sys._getframe().f_back.f_globals.get("__file__")
    if file is None or file[0] == "<":
        return [_Path.cwd() / i for i in paths]
    parent = _Path(file).parent
    return [
        parent / i if isinstance(i, _Path) and not i.is_absolute() else i
        for i in paths
    ]


def hide_from_PATH(name):
    """Modify ``PATH`` from :data:`os.environ` so that **name** can't be found.

    Args:
        name (str): The executable name to hide.

    Returns:
        str: The original value of :py:`os.environ['PATH']`.

    """
    import os
    import shutil
    old = os.environ["PATH"]
    paths = old.split(os.pathsep)
    paths = [i for i in paths if shutil.which(name, path=i) is None]
    os.environ["PATH"] = os.pathsep.join(paths)
    return old


def flatten(iterable, types=(tuple, list), initial=None):
    """Collapse nested iterables into one flat :class:`list`.

    Args:
        iterable:
            Nested container.
        types:
            Type(s) to be collapsed. This argument is passed directly to
            :func:`isinstance`.
        initial:
            A pre-existing :class:`list` to append to. An empty list is created
            if one is not supplied.

    Returns:
        list: The flattened output.

    ::

        >>> flatten([[1, 2], 3, [4, [5]]])
        [1, 2, 3, 4, 5]
        >>> flatten(1.0)
        [1.0]
        >>> flatten([(1, 2), 3, (4, 5)])
        [1, 2, 3, 4, 5]
        >>> flatten([(1, 2), 3, (4, 5)], types=list)
        [(1, 2), 3, (4, 5)]
        >>> flatten([(1, 2), 3, (4, 5)], initial=[6, 7])
        [6, 7, 1, 2, 3, 4, 5]

    """
    if initial is None:
        initial = []
    if isinstance(iterable, types):
        for i in iterable:
            flatten(i, types, initial)
    else:
        initial.append(iterable)
    return initial


@_contextlib.contextmanager
def block_compile():
    """Temporarily block |cslug| compilation.

    A context manager to temporarly set the ``CC`` environment variable to
    ``!block`` which is a signal to |cslug| that it is not allowed to use any
    C compiler.

    ::

        >>> from cslug import cc, misc
        >>> cc()
        'c:\\MinGW\\bin\\gcc.EXE'
        >>> with misc.block_compile():
        ...     cc()
        cslug.exceptions.BuildBlockedError: The build was blocked by the
        environment variable `CC=block`.

    This is only meant for testing.

    """
    import os
    old = os.environ.get("CC")
    os.environ["CC"] = "!block"
    try:
        yield
    finally:
        if old is None:
            del os.environ["CC"]
        else:
            os.environ["CC"] = old


def array_typecode(c_name):
    """Choose a type code for :class:`array.array`.

    Args:
        c_name (str): The name you would use in C to define the type.

    Returns:
        str: Any of :data:`array.typecodes`.

    Use this function to normalise aliases and platform specific exact types.

    Examples:
        >>> array_typecode("long")
        'l'
        >>> array_typecode("double")
        'd'
        >>> array_typecode("uint64_t")
        'Q'
        >>> array_typecode("size_t")
        'Q'

    """
    out = _array_typecode(c_name)
    if out is None:
        raise ValueError(f"Unrecognised or unsupported type '{c_name}'.")
    return out


@_funtiontools.lru_cache()
def _array_typecode(c_name: str):
    """The workhorse behind :func:`array_typecode`.

    The only difference is that this function returns None rather than raising
    an error if it can't find a typecode. Splitting into two allows this
    function to call itself with normalised inputs without having to remember
    the original value of **c_name** to include in any error messages.
    """
    import ctypes
    if c_name.startswith("unsigned "):
        # Unsigned typecodes are the same as their signed types but upper-cased.
        return _array_typecode(c_name[9:]).upper()

    # XXX: Can be replaced with str.removeprefix() in Python 3.9
    # Remove `signed ` prefix.
    c_name = _re.fullmatch(r"(?:signed )?(.*)", c_name).group(1)
    # Remove `c_` prefix and `_t` suffix.
    c_name = _re.fullmatch(r"(?:c_)?(.+?)(?:_t)?", c_name).group(1)
    # Ignore the word ` int` if there are other words in front of it.
    c_name = _re.fullmatch(r"(.+?)(?: int)?", c_name).group(1)
    # Collapse any spaces.
    c_name = c_name.replace(" ", "")

    if c_name in _ARRAY_TYPECODES:
        return _ARRAY_TYPECODES[c_name]

    # ctypes has already normalised exact types to the more standard types.
    # e.g. `ctypes.c_int16` is just an alias for `ctypes.c_short` so
    # `ctypes.c_int16.__name__` will give `c_short`.
    ctypes_name = "c_" + c_name
    if hasattr(ctypes, ctypes_name):
        c_name = getattr(ctypes, ctypes_name).__name__
        c_name = c_name[2:]

    if c_name in _ARRAY_TYPECODES:
        return _ARRAY_TYPECODES[c_name]

    if c_name.startswith("u") and c_name[1:] in _ARRAY_TYPECODES:
        return _ARRAY_TYPECODES[c_name[1:]].upper()


_ARRAY_TYPECODES = {
    "char": "b",
    "short": "h",
    "int": "i",
    "long": "l",
    "longlong": "q",
    "float": "f",
    "double": "d",
    "byte": "b",
}

_ARRAY_TYPECODES["ssize"] = array_typecode(_ctypes.c_ssize_t.__name__)
_ARRAY_TYPECODES["size"] = _ARRAY_TYPECODES["ssize"].upper()
