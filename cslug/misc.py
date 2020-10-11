# -*- coding: utf-8 -*-
"""
"""

import io
from pathlib import Path


def as_path_or_buffer(file):
    return file if isinstance(file, io.IOBase) else Path(file)


def exists_or_buffer(file):
    return isinstance(file, io.IOBase) or file.exists()


def read(path, mode="r"):
    if isinstance(path, io.IOBase):
        return path.read(), None
    with open(path, mode, encoding="utf-8") as f:
        return f.read(), path


def write(path, *data, mode="w"):
    if isinstance(path, io.IOBase):
        return path.writelines(data)
    with open(path, mode, encoding="utf-8") as f:
        return f.writelines(data)
