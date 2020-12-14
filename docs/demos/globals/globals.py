# -*- coding: utf-8 -*-
"""
This ugly mess doubles as a source of code snippets to be embedded in the
globals.rst docs and a test.
"""

import os

os.chdir(os.path.dirname(__file__))

import ctypes
from cslug import CSlug, _cc

slug = CSlug("globals.c")

slug.make()
# yapf: disable

an_int = ctypes.cast(slug.dll.an_int, ctypes.POINTER(ctypes.c_int)).contents
assert an_int.value == 42
an_int.value += 5
assert slug.dll.get_an_int() == an_int.value

a_float = ctypes.cast(slug.dll.a_float, ctypes.POINTER(ctypes.c_float)).contents
a_double = ctypes.cast(slug.dll.a_double, ctypes.POINTER(ctypes.c_double)).contents
an_8_bit_int = ctypes.cast(slug.dll.an_8_bit_int, ctypes.POINTER(ctypes.c_int8)).contents

assert abs(a_float.value - 1 / 3) < 1e-5
assert abs(a_double.value - 1 / 3) < 1e-12
assert an_8_bit_int.value == 43

a_bytes_array = ctypes.cast(slug.dll.a_bytes_array, ctypes.c_char_p)
a_string = ctypes.cast(slug.dll.a_string, ctypes.c_wchar_p)

assert a_bytes_array.value == b"Hello, my name is Ned."
if a_string.value != "Сәлам. Минем исемем Нед.":
    if _cc.cc_version()[0] != "tcc":
        raise AssertionError(
            f"{repr(a_string.value)} != \"Сәлам. Минем исемем Нед.\"")


contains_null = ctypes.cast(slug.dll.contains_null, ctypes.c_char_p)

assert contains_null.value == b"This sentence has a "

# Extract the length (just a regular int).
length = ctypes.cast(slug.dll.len_contains_null, ctypes.POINTER(ctypes.c_int)).contents.value

# Get a raw void (untyped) pointer to our string.
address = ctypes.cast(slug.dll.contains_null, ctypes.c_void_p).value

# Interpret the pointer as an array of the correct length.
contains_null = (ctypes.c_char * length).from_address(address)

assert contains_null.raw == b"This sentence has a \x00 in the middle of it.\x00"
