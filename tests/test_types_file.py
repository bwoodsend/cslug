# -*- coding: utf-8 -*-
"""
"""
import io
import json
import warnings
import ctypes

import pytest

import cslug
from tests import filter_warnings

SOURCE = """
// Something simple.
void simple() {}

// Arguments of just ``void`` should be ignored.
bool voids(void, void, void) {}

// Some random types.
int foo(char x) {}
float bar(int32_t a, int16_t b, uint64_t c) {}
short whack(unsigned long d, double e, long) {}

// All pointers reduce to just void pointer.
void * ptrs(float * a, int **, * Custom, *Custom, Custom*, Custom  *  ) {}
// Except for char arrays which get their own pointer types.
void char_ptr(char [], char *, wchar_t*) {}
// But pointers to char pointers are reduced to just void pointers.
void char_ptr_ptr(char [][], char **, *wchar_t*) {}

// Invalid syntax defaults to ``None`` - leave the compiler to raise any issues.
char invalid_argument(I like cake) {}
// Likewise with invalid types.
void invalid_argument_2(long long long) {}

// Unicode shouldn't break anything...
byte unicode_ÀÆÌÐÔÙÝáåéíñõùý(شيء * مخصص, 習俗 ** 事情) {}

// Some red herrings that look vaguely like function definitions.
return f();
for (int i = 0; i < 10; i++) {}
else if() {}

// Windows only type aliases.
SIZE_T windows_aliases(WORD a, DWORD b, QWORD c) {}
LPSTR windows_ptr_aliases(LPCSTR a, LPVOID b) {}

"""

PARSED_FUNCTIONS = {
    'simple': ['None', []],
    #
    'voids': ['c_bool', []],
    #
    'foo': ['c_int', ['c_char']],
    'bar': ['c_float', ['c_int32', 'c_int16', 'c_uint64']],
    'whack': ['c_short', ['c_ulong', 'c_double', 'c_long']],
    #
    'ptrs': ['c_void_p', ['c_void_p'] * 6],
    'char_ptr': ['None', ['c_char_p', 'c_char_p', 'c_wchar_p']],
    'char_ptr_ptr': ['None', ['c_void_p', 'c_void_p', 'c_void_p']],
    #
    'invalid_argument': ['c_char', ['None']],
    'invalid_argument_2': ['None', ['None']],
    #
    'unicode_ÀÆÌÐÔÙÝáåéíñõùý': ['c_byte', ['c_void_p', 'c_void_p']],
    #
    'windows_aliases': ['c_size_t', ['c_int16', 'c_int32', 'c_int64']],
    'windows_ptr_aliases': ['c_char_p', ['c_char_p', 'c_void_p']],
}


@pytest.mark.parametrize("modifier",
                         [lambda x: x, lambda x: x.replace("{", "\n{")])
def test_functions(modifier):
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore",
                                category=cslug.exceptions.TypeParseWarning)

        self = cslug.Types(io.StringIO(), io.StringIO(modifier(SOURCE)))
        self.make()
        assert self.functions == PARSED_FUNCTIONS
        assert json.loads(
            self.json_path.getvalue())["functions"] == PARSED_FUNCTIONS
        from_json = cslug.Types(io.StringIO(self.json_path.getvalue()))
        from_json.init_from_json()
        assert from_json.types == self.types


@pytest.mark.parametrize(
    "modifier",
    [lambda x: x.replace("{}", ";"), lambda x: x.replace("{", ";{")])
def test_ignores_prototypes(modifier):
    self = cslug.Types(io.StringIO(), io.StringIO(modifier(SOURCE)))
    self.init_from_source()
    assert not self.functions


STRUCT_TEXT = """
typedef struct spam
{
    char a;
    int b;
    int c:3;
    unsigned int d: 4;
} Test;
"""

PARSED_STRUCTS = {
    'Test': [('a', 'c_char'), ('b', 'c_int'), ('c', 'c_int', 3),
             ('d', 'c_uint', 4)]
}

STRUCT_METHODS = """
Test returns_test() {}
Test * returns_test_ptr() {}
void takes_test(Test t) {}
void takes_test_ptr(Test * t) {}
"""

PARSED_STRUCT_METHODS = {
    'returns_test': ['Test', []],
    'returns_test_ptr': ['c_void_p', []],
    'takes_test': ['None', ['Test']],
    'takes_test_ptr': ['None', ['c_void_p']],
}


def test_struct():
    self = cslug.Types(io.StringIO(), io.StringIO(STRUCT_TEXT + STRUCT_METHODS))
    self.make()
    assert self.structs == PARSED_STRUCTS
    assert self.functions == PARSED_STRUCT_METHODS


@filter_warnings("ignore", category=cslug.exceptions.TypeParseWarning)
def test_prototypes():
    prototype_source = io.StringIO(SOURCE.replace("{}", ";"))

    # Prototypes should be ignored by default.
    self = cslug.Types(io.StringIO(), prototype_source)
    assert self._types_from_source()["functions"] == {}

    # Unless they are passed as headers to intentionally include prototypes.
    self = cslug.Types(io.StringIO(), headers=prototype_source)
    assert self._types_from_source()["functions"] == PARSED_FUNCTIONS


def test_struct_prototypes():
    # Check structs are correctly linked.
    struct_prototypes = io.StringIO(STRUCT_METHODS.replace("{}", ";"))
    self = cslug.Types(io.StringIO(),
                       headers=[struct_prototypes,
                                io.StringIO(STRUCT_TEXT)])
    self.init_from_source()
    assert self.structs == PARSED_STRUCTS
    assert self.functions == PARSED_STRUCT_METHODS

    # The same test but pass the struct definition as a true source.
    # Should make no difference.
    struct_prototypes = io.StringIO(STRUCT_METHODS.replace("{}", ";"))
    self = cslug.Types(io.StringIO(), io.StringIO(STRUCT_TEXT),
                       headers=struct_prototypes)
    self.init_from_source()
    assert self.structs == PARSED_STRUCTS
    assert self.functions == PARSED_STRUCT_METHODS


@pytest.mark.parametrize("strict", [0, 1])
def test_strict(strict):
    class FakeDLL(object):
        exists = ctypes.PYFUNCTYPE(int)()

    self = cslug.Types(
        io.StringIO(), headers=io.StringIO("""
        float exists(int x);
        float doesnt_exist(int x);
        double also_doesnt_exist(float y);
    """))

    self.init_from_source()
    dll = FakeDLL()

    if not strict:
        # Should skip over non-existent functions without complaint.
        self.apply(dll)
    else:
        # Should raise an error.
        with pytest.raises(
                AttributeError,
                match=r".* \['doesnt_exist', 'also_doesnt_exist'] .*"):
            self.apply(dll, strict=True)

    assert dll.exists.argtypes == [ctypes.c_int]
    assert dll.exists.restype == ctypes.c_float
    assert not hasattr(dll, "doesnt_exist")
    assert not hasattr(dll, "also_doesnt_exist")
