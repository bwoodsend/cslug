# -*- coding: utf-8 -*-
"""
"""
import io
import json
import warnings

import pytest

import cslug

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
        assert self.types["functions"] == PARSED_FUNCTIONS
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
    assert not self.types["functions"]


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


def test_struct():
    self = cslug.Types(io.StringIO(), io.StringIO(STRUCT_TEXT))
    self.make()
    assert not self.types["functions"]
    assert self.types["structs"] == PARSED_STRUCTS
