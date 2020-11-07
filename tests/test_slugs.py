# -*- coding: utf-8 -*-
"""
"""

import os, sys
from pathlib import Path
import uuid
import io
import ctypes
import fnmatch

import pytest

from cslug import exceptions, anchor, CSlug, misc

DUMP = anchor("dump")[0]
DUMP.mkdir(exist_ok=True)

pytestmark = pytest.mark.last


def name():
    return Path("dump", str(uuid.uuid1()))


def test_basic():
    self = CSlug(*anchor(name(), io.StringIO("""
        int add_1(int x) { return x + 1; }

        float times_2(float y) { return y * 2.0; }

        """))) # yapf: disable

    assert not self.path.exists()
    assert not self.types_dict.json_path.exists()
    self.dll
    assert self.path.exists()
    assert self.types_dict.json_path.exists()

    assert hasattr(self.dll, "add_1")
    assert hasattr(self.dll, "times_2")

    assert self.dll.add_1.restype == ctypes.c_int
    assert self.dll.add_1.argtypes == [ctypes.c_int]
    assert self.dll.times_2.restype == ctypes.c_float
    assert self.dll.times_2.argtypes == [ctypes.c_float]

    assert isinstance(self.dll.add_1(3), int)
    assert self.dll.add_1(3) == 4
    assert isinstance(self.dll.times_2(6), float)
    assert self.dll.times_2(7.5) == 15
    assert self.dll.times_2(7) == 14.0

    with pytest.raises(Exception):
        self.dll.add_1()
    with pytest.raises(Exception):
        self.dll.add_1(2.0)


def test_propagate_build_warnings():

    self = CSlug(*anchor(
        name(), io.StringIO("""
        int foo() { return 1 / 0; }
        """)))

    with pytest.warns(exceptions.BuildWarning):
        self.make()

    assert hasattr(self.dll, "foo")


def test_build_error():

    self = CSlug(*anchor(
        name(), io.StringIO("""
        int invalid() { syntax }
        """)))

    with pytest.raises(exceptions.BuildError):
        self.make()

    assert getattr(self, "_dll", None) is None


def test_no_gcc_error():

    self = CSlug(*anchor(name(), io.StringIO("")))

    old = misc.hide_from_PATH("gcc")
    try:
        with pytest.raises(exceptions.NoGccError):
            self.make()
    finally:
        os.environ["PATH"] = old

    assert self.make()


def test_exception_str():
    str(exceptions.BuildError("foo", "bar"))
    str(exceptions.NoGccError())


def test_io_dll():
    """Not supported."""
    with pytest.raises(TypeError):
        CSlug(io.BytesIO())


def test_implicit_dll_name():
    self = CSlug("file.c")
    assert fnmatch.fnmatch(self.path.stem, "file-*-*bit")
    assert self.path.suffix != ".c"
    assert self.sources == [Path("file.c")]


def test_no_anchor():
    old_cwd = os.getcwd()
    try:
        os.chdir(DUMP)
        self = CSlug(name().name, io.StringIO(""))
        # The path eventually given to CDLL must not be just a name. i.e. It
        # can either be absolute, include a folder name e.g. `foo/bar` or
        # prefixed with `./`. In all these cases, `os.path.dirname()` will emit
        # a non-empty string.
        assert os.path.dirname(self.dll._name)

    finally:
        os.chdir(old_cwd)
