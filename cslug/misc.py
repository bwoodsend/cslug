# -*- coding: utf-8 -*-
"""
"""

import io
import sys
import re
from pathlib import Path


def as_path_or_buffer(file):
    return file if isinstance(file, io.IOBase) else Path(file)


def as_path_or_readable_buffer(file):
    if isinstance(file, io.IOBase):
        if hasattr(file, "getvalue"):
            return file
        return io.StringIO(file.read())
    return Path(file)


def _read(path, mode="r"):
    if isinstance(path, io.IOBase):
        if hasattr(path, "getvalue"):
            return path.getvalue(), None
        return path.read(), None
    with open(path, mode, encoding="utf-8") as f:
        return f.read(), path


def read(path, mode="r"):
    text, path = _read(path, mode)
    if mode == "r":
        text = re.sub("\r\n?", "\n", text)
    return text, path


def write(path, *data, mode="w"):
    if isinstance(path, io.IOBase):
        return path.writelines(data)
    with open(path, mode, encoding="utf-8") as f:
        return f.writelines(data)


def anchor(*paths):
    """Replace relative paths with frozen paths relative to ``__file__``\\ 's
    parent.

    :param paths: Path(s) to freeze or pseudo files.
    :type paths: str, os.PathLike, io.IOBase
    :return: List of modified paths.
    :rtype: list[pathlib.Path, io.IOBase]

    Pseudo files (:class:`io.IOBase`) and absolute paths are left unchanged. Use
    this function to make your code working-dir independent.
    """
    paths = map(as_path_or_buffer, paths)
    file = sys._getframe().f_back.f_globals.get("__file__")
    if file is None or file[0] == "<":
        return [Path.cwd() / i for i in paths]
    parent = Path(file).parent
    return [
        parent / i if isinstance(i, Path) and not i.is_absolute() else i
        for i in paths
    ]


def hide_from_PATH(name):
    import os
    import shutil
    old = os.environ["PATH"]
    paths = old.split(os.pathsep)
    paths = [i for i in paths if shutil.which(name, path=i) is None]
    os.environ["PATH"] = os.pathsep.join(paths)
    return old


def flatten(iterable, types=(tuple, list), initial=None):
    if initial is None:
        initial = []
    if isinstance(iterable, types):
        for i in iterable:
            flatten(i, types, initial)
    else:
        initial.append(iterable)
    return initial
