# -*- coding: utf-8 -*-
"""
"""

import io
import sys
from pathlib import Path


def as_path_or_buffer(file):
    return file if isinstance(file, io.IOBase) else Path(file)


def as_path_or_readable_buffer(file):
    if isinstance(file, io.IOBase):
        if hasattr(file, "getvalue"):
            return file
        return io.StringIO(file.read())
    return Path(file)


def exists_or_buffer(file):
    return isinstance(file, io.IOBase) or file.exists()


def read(path, mode="r"):
    if isinstance(path, io.IOBase):
        if hasattr(path, "getvalue"):
            return path.getvalue(), None
        return path.read(), None
    with open(path, mode, encoding="utf-8") as f:
        return f.read(), path


def write(path, *data, mode="w"):
    if isinstance(path, io.IOBase):
        return path.writelines(data)
    with open(path, mode, encoding="utf-8") as f:
        return f.writelines(data)
