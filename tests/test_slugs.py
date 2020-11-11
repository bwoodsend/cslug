# -*- coding: utf-8 -*-
"""
"""

import os, sys
from pathlib import Path
import io
import ctypes
import fnmatch

import pytest

from cslug import exceptions, anchor, CSlug, misc

from tests import DUMP, name

pytestmark = pytest.mark.order(-3)


@pytest.mark.order(0)
@pytest.mark.parametrize("true_file", [True, False])
def test_basic(true_file):
    SOURCE = """
    int add_1(int x) { return x + 1; }
    float times_2(float y) { return y * 2.0; }
    """
    if true_file:
        file = DUMP / "basic.c"
        file.write_text(SOURCE)
    else:
        file = io.StringIO(SOURCE)
    self = CSlug(*anchor(name(), file)) # yapf: disable

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


def test_printf_warns():
    from cslug._cdll import check_printfs

    assert not check_printfs("//printf(stuff)")
    assert not check_printfs("  //  \tprintf(stuff)")
    assert not check_printfs("/*\n\nprintf(stuff)\n*/")

    with pytest.warns(exceptions.PrintfWarning, match='.* at "<string>:0".*'):
        assert check_printfs("printf(stuff)")
    with pytest.warns(exceptions.PrintfWarning, match='.* at "name.c:0".*'):
        assert check_printfs("printf(stuff)", "name.c")
    with pytest.warns(exceptions.PrintfWarning):
        assert check_printfs("printf(stuff)//")
    with pytest.warns(exceptions.PrintfWarning, match='.* at "<string>:102".*'):
        assert check_printfs("# 100\n\nprintf()")


def test_names_not_in_dll():
    """
    Check that CSlug doesn't get into too much of a mess if it thinks a
    function should exist but doesn't.
    """

    # Both the functions in the C source below look to cslug like they would be
    # included in the DLL but in fact aren't.
    self = CSlug(*anchor(name(), io.StringIO("""

        inline int add_1(int x) { return x + 1; }

        #if 0
        float times_2(float y) { return y * 2.0; }
        #endif

    """))) # yapf: disable

    # Ensure built:
    self.dll

    # Check cslug found them.
    assert "add_1" in self.types_dict.types["functions"]
    assert "times_2" in self.types_dict.types["functions"]

    # But they are not in the DLL.

    # Inline functions may still be present. I believe this is gcc version
    # dependent.
    # assert not hasattr(self.dll, "add_1")
    # with pytest.raises(AttributeError):
    #     self.dll.add_1

    assert not hasattr(self.dll, "times_2")
    with pytest.raises(AttributeError):
        self.dll.time_2


def test_bit_ness():
    from cslug._cdll import BIT_NESS

    self = CSlug(*anchor(name(), io.StringIO("""

        # include <stddef.h>
        # include <stdbool.h>

        bool add_1_overflows(size_t x) {
            return (x + 1) < x;
        }

    """))) # yapf: disable

    def add_1_overflows(x):
        x = ctypes.c_size_t(x).value
        return ctypes.c_size_t(x + 1).value < x

    if BIT_NESS == 64:
        assert add_1_overflows((1 << 64) - 1)
        assert self.dll.add_1_overflows((1 << 64) - 1)

        assert not add_1_overflows((1 << 32) - 1)
        assert not self.dll.add_1_overflows((1 << 32) - 1)

    else:
        assert add_1_overflows((1 << 32) - 1)
        assert self.dll.add_1_overflows((1 << 32) - 1)
