# -*- coding: utf-8 -*-
"""
"""

import ctypes

import pytest

from cslug import ptr

pytestmark = pytest.mark.order(-2)


@pytest.mark.parametrize("binary", range(2))
def test_character_arrays_dont_need_null_termination(binary):
    """
    Test that a C string converted to Python doesn't need to be null terminated.

    I make this rather heavy assumption that it's ok in the docs. If this fails
    then a lot of examples are wrong.
    """
    char = ctypes.c_char if binary else ctypes.c_wchar

    text = str(copyright)
    assert "\x00" not in text
    if binary:
        text = text.encode()
        assert b"\x00" not in text
        array = ctypes.create_string_buffer(text)
    else:
        array = ctypes.create_unicode_buffer(text)

    for i in range(100):
        unterminated = (char * i).from_address(ptr(array)._as_parameter_)
        value = unterminated.value
        assert len(value) == i
        assert value == text[:i]
