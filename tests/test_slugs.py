# -*- coding: utf-8 -*-
"""
"""

import os, sys
from pathlib import Path
import io
import ctypes
import fnmatch
import itertools
import random
import platform

import pytest

from cslug import exceptions, anchor, CSlug, misc, Header

from tests import DUMP, name, DEMOS, RESOURCES
from tests.test_pointers import leaks

pytestmark = pytest.mark.order(-3)


@pytest.mark.order(-4)
@pytest.mark.parametrize("true_file", [True, False])
def test_basic(true_file):
    SOURCE = RESOURCES / "basic.c"
    if true_file:
        file = SOURCE
    else:
        file = io.StringIO(SOURCE.read_text())
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

    self = CSlug(*anchor(name(), io.StringIO("""
        #warning "Not a good idea."
        void foo() {  }
    """))) # yapf: disable

    with pytest.warns(exceptions.BuildWarning, match="Not a good idea."):
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


def test_no_cc_or_blocked_error():

    self = CSlug(*anchor(name(), io.StringIO("")))

    old = os.environ.copy()
    try:
        misc.hide_from_PATH("gcc")
        os.environ.pop("CC", None)
        with pytest.raises(exceptions.NoGccError):
            self.make()
    finally:
        os.environ.clear()
        os.environ.update(old)

    with pytest.raises(exceptions.BuildBlockedError):
        with misc.block_compile():
            self.make()
    str(exceptions.BuildBlockedError())

    assert self.make()


def test_exception_str():
    str(exceptions.BuildError("foo", "bar"))
    str(exceptions.NoGccError())
    assert "/a/file" in str(exceptions.LibraryOpenElsewhereError("/a/file"))


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
    from cslug._cslug import check_printfs

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
    assert "add_1" in self.types_dict.functions
    assert "times_2" in self.types_dict.functions

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
    """Check 32/64b-bits behaves as expected by looking at integer overflow.
    """
    from cslug._cslug import BIT_NESS

    self = CSlug(*anchor(name(), io.StringIO("""

        # include <stddef.h>
        # include <stdbool.h>

        bool adding_1_causes_overflow(size_t x) {
            return (x + 1) < x;
        }

    """))) # yapf: disable

    for int_size in range(8, 128, 8):
        # Maximum possible value for an unsigned int of size ``int_size``.
        int_max = (1 << int_size) - 1
        if BIT_NESS <= int_size:
            assert adding_1_causes_overflow_py(int_max)
            assert self.dll.adding_1_causes_overflow(int_max)

        else:
            assert not adding_1_causes_overflow_py(int_max)
            assert not self.dll.adding_1_causes_overflow(int_max)


def adding_1_causes_overflow_py(x):
    x = ctypes.c_size_t(x).value
    return ctypes.c_size_t(x + 1).value < x


def test_str():
    self = CSlug(anchor(name()), DEMOS / "strings" / "reverse.c")
    self.make()

    def reverse_test(text):
        out = ctypes.create_unicode_buffer(len(text) + 1)
        self.dll.reverse(text, out, len(text)) is None
        assert out.value == text[::-1]
        assert out[:] == text[::-1] + "\x00"

    reverse_test("hello")

    # A 10th of the memory that would be leaked if `reverse_test()` leaked.
    tolerance = ctypes.sizeof(ctypes.create_unicode_buffer("hello" * 100)) * 10
    leaks(lambda: reverse_test("hello" * 100), n=100, tol=tolerance)


def test_bytes():
    self = CSlug(anchor(name()), DEMOS / "bytes" / "encrypt.c")
    self.make()

    def _crypt(data, key, multiplier):
        out = ctypes.create_string_buffer(len(data))
        self.dll.encrypt(data, len(data), out, key, len(key), multiplier)
        return out[:]

    def encrypt(data, key):
        return _crypt(data, key, 1)

    def decrypt(data, key):
        return _crypt(data, key, -1)

    data = bytes(range(256))
    key = b"secret"
    encrypted = encrypt(data, key)
    assert isinstance(encrypted, bytes)

    # A pure Python equivalent of the C code we're testing.
    pure_py = bytes((i + j) % 256 for (i, j) in zip(data, itertools.cycle(key)))
    assert encrypted == pure_py

    assert decrypt(encrypted, key) == data
    leaks(lambda: encrypt(data, key), n=100, tol=len(data) * 10)


def test_header_type_error():
    with pytest.raises(TypeError):
        CSlug("name", headers="not a header")


def test_with_header():
    header_name = "header-" + name().stem + ".h"
    cake = random.randint(0, 256)
    header = Header(DUMP / header_name, defines={"cake": cake})

    source, = anchor(name().with_suffix(".c"))
    source.write_text("""\
    #include "%s"

    int get_cake() {
        return cake;
    }
    """ % header_name)

    self = CSlug(*anchor(name()), source, headers=header)  # yapf: disable

    try:
        old = os.getcwd()
        os.chdir(DUMP)
        self.make()
    finally:
        os.chdir(old)

    assert self.headers[0].path.exists()
    assert self.dll.get_cake() == cake


def test_remake():
    from cslug._stdlib import dlclose, null_free_dll, stdlib
    assert dlclose is not null_free_dll, \
        "A `dlclose()` function hasn't been found for this platform. It "\
        "should be added to `_cslug._stdlib.py`."

    slug = CSlug(anchor(name(), RESOURCES / "basic.c"))
    path = slug.dll._name

    # Having the DLL open should block writing to it on Windows.
    ref = ctypes.CDLL(path)

    try:
        slug.make()
    except exceptions.LibraryOpenElsewhereError as ex:
        # This will happen only on Windows.
        assert path in str(ex)

    if platform.system() == "FreeBSD":
        # dlclose() seems to complain no matter what I do with it.
        stdlib.dlerror.restype = ctypes.c_char_p
        # This fails with an unhelpful b"Service unavailable".
        # assert dlclose(ctypes.c_void_p(ref._handle)) == 0, stdlib.dlerror()
        # dlclosing is mainly for Windows, which causes Permission errors if
        # you forget it. As far as I know, this issue is harmless.
    else:
        assert dlclose(ctypes.c_void_p(ref._handle)) == 0

    # With the DLL closed make() should work.
    slug.make()

    # Each slug gets registered in `_slug_refs`. Check that this has happened.
    # `slug` should be the only one registered under this filename.
    from cslug._cslug import _slug_refs
    assert slug.path in _slug_refs
    assert len(_slug_refs[slug.path]) == 1
    assert _slug_refs[slug.path][0]() is slug

    # Create another slug with the same filename. It should join the 1st in the
    # register.
    other = CSlug(slug.name, *slug.sources)
    assert other.path == slug.path
    assert len(_slug_refs[slug.path]) == 2
    assert _slug_refs[slug.path][1]() is other

    # Get `other` to open its DLL.
    other_dll = other.dll
    assert other_dll.add_1(2) == 3
    # Make `slug` try to rebuild the DLL which is already opened by `other`.
    # This would normally cause mayhem but doesn't because `slug.make()`
    # implicitly calls`other.close()` so that it doesn't try to overwrite an
    # open file.
    slug.make()
    # `other.dll` should re-open automatically.
    assert other.dll is not other_dll

    # `other` is weakref-ed and should still be garbage-collectable despite
    # being in `_slug_refs`.
    del other_dll, other
    # Test the link in `_slug_refs` is dead.
    assert _slug_refs[slug.path][1]() is None

    # `_slug_refs` should be cleared of dead links on calling `close()`.
    slug.close()
    assert len(_slug_refs[slug.path]) == 1


def test_link():
    # TODO: This isn't much of a test. Try to think of a cross platform library
    #       to link against. Or a non cross platform library for each OS.
    self = CSlug(RESOURCES / "basic.c", links="c")
    if platform.system() == "Linux":
        assert self.links == ["c", "m"]
    else:
        assert self.links == ["c"]
    assert "-lc" in self.compile_command()[0]


def test_default_link():
    # 'm' should always be linked to on Linux.
    self = CSlug(RESOURCES / "basic.c")
    if platform.system() == "Linux":
        assert "-lm" in self.compile_command()[0]

    # A library that is added both explicitly add by default should not be
    # duplicated.
    self = CSlug(RESOURCES / "basic.c", links="m")
    assert self.compile_command()[0].count("-lm") == 1
