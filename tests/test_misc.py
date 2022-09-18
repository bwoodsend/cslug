import os, sys
from pathlib import Path
import random
import io
from array import array
import ctypes

import pytest

import cslug
from cslug.misc import read, as_path_or_readable_buffer, block_compile, \
    array_typecode

from tests import RESOURCES


def random_dir():
    """
    Pick a random existing folder that we have sufficient permission to access.

    """
    path = Path.home().resolve()
    for i in range(10):
        for _path in path.glob("*"):
            if _path.is_dir() and random.random() < .3:
                try:
                    os.listdir(_path)
                    _path.is_dir()
                    path = _path.resolve()
                except PermissionError:
                    continue

    return path


random_dirs = [random_dir() for i in range(3)]


@pytest.mark.parametrize("test_dir", random_dirs)
def test_unanchored(test_dir):
    _test_anchor(test_dir, test_dir, {})
    _test_anchor(test_dir, test_dir, {"__file__": "<string>"})


THIS_FILE = Path(__file__).resolve()


@pytest.mark.parametrize("test_dir", random_dirs)
def test_anchored(test_dir):
    _test_anchor(test_dir, THIS_FILE.parent, {"__file__": str(THIS_FILE)})


def _test_anchor(test_dir, prefix, namespace):
    old_wd = Path.cwd()
    target = [prefix, prefix / "hello", prefix / "foo" / "bar"]

    try:
        os.chdir(test_dir)

        namespace["cslug"] = cslug
        exec("paths = cslug.anchor('.', 'hello', 'foo/bar')", namespace)
        assert namespace["paths"] == target

    finally:
        os.chdir(old_wd)


def test_read():
    """
    Test :meth:`cslug.misc.read`.
    """
    path = RESOURCES / "to_headerise.c"
    target = path.read_text()

    # Read from an open file handle without closing it.
    with open(path) as f:
        assert read(f) == (target, None)
        assert not f.closed
        assert isinstance(as_path_or_readable_buffer(f), io.StringIO)
    assert f.closed

    file = io.StringIO(target)
    assert read(file) == (target, None)
    assert as_path_or_readable_buffer(file) is file

    # `read()` should avoid consuming a file's buffer if it can get away
    # without.
    assert read(file) == (target, None)
    assert file.read() == target

    assert read(path) == (target, path)
    assert read(str(path)) == (target, str(path))


@pytest.mark.parametrize("ending", ["\r", "\n", "\r\n"])
def test_read_crlf(ending):
    TEXT = str(copyright)
    assert "\r" not in TEXT
    assert read(io.StringIO(TEXT.replace("\n", ending))) == (TEXT, None)

    BINARY = TEXT.replace("\n", ending).encode()
    assert read(io.BytesIO(BINARY), "rb") == (BINARY, None)


def test_block_compile():
    old = os.environ.get("CC")

    os.environ["CC"] = "cake"
    with block_compile():
        assert os.environ.get("CC") == "!block"
    assert os.environ.get("CC") == "cake"

    del os.environ["CC"]
    with block_compile():
        assert os.environ.get("CC") == "!block"
    assert "CC" not in os.environ

    if old is not None:
        os.environ["CC"] = old

    assert os.environ.get("CC") == old


def test_array_typecodes():
    # Basic types from
    # https://docs.python.org/3/library/array.html#module-array
    int_types = "il" if ctypes.c_int is ctypes.c_long else "i"
    assert array_typecode("int") in int_types
    assert array_typecode("signed int") in int_types
    assert array_typecode("unsigned int") in int_types.upper()
    assert array_typecode("uint") in int_types.upper()
    assert array_typecode("int_t") in int_types
    assert array_typecode("c_int") == "i"
    assert array_typecode("short") == "h"
    assert array_typecode("short int") == "h"
    assert array_typecode("long") == "l"
    assert array_typecode("unsigned long long") == "Q"
    assert array_typecode("longlong") == "q"
    assert array_typecode("byte") == "b"
    assert array_typecode("char") == "b"
    assert array_typecode("signed char") == "b"
    assert array_typecode("unsigned char") == "B"
    assert array_typecode("uchar") == "B"
    assert array_typecode("float") == "f"
    assert array_typecode("double") == "d"

    # Platform specific aliases that cslug has used ctypes to follow.
    _test_exact_type("int8", 1)
    _test_exact_type("uint8", 1, signed=False)
    _test_exact_type("int16", 2)
    _test_exact_type("int32_t", 4)
    _test_exact_type("int64", 8)
    _test_exact_type("size", ctypes.sizeof(ctypes.c_size_t), signed=False)
    _test_exact_type("ssize", ctypes.sizeof(ctypes.c_size_t))

    with pytest.raises(ValueError, match="'int33'"):
        array_typecode("int33")
    with pytest.raises(ValueError):
        array_typecode("signed bagel")


def _test_exact_type(name, size, signed=True):
    code = array_typecode(name)
    assert array(code).itemsize == size
    assert code.islower() is signed
