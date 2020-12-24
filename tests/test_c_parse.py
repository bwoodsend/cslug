# -*- coding: utf-8 -*-
"""
"""

import os, sys
from pathlib import Path
import re

import pytest

import cslug

pytestmark = pytest.mark.order(0)

ALL_TOKEN_TYPE_PERMUTATIONS = range(
    max(cslug.c_parse.TokenType.__members__.values()) * 2)

SOURCES = r"""

code "literal" // comment
code

'literal'

"literal\"still a literal // literal /*literal/*"

/* comment "comment" \comment // comment
comment */

// "comment"

"invalid literal

/* unterminated comment

""".split("\n\n")


def _assert_counts_match(source, stripped, token_types):
    for token_type in cslug.c_parse.TokenType:
        if token_types & token_type:
            name = token_type.name.lower()
            assert source.count(name) == stripped.count(name)


def test_test():
    with pytest.raises(AssertionError):
        test_filter("// literal", cslug.c_parse.TokenType.LITERAL)


@pytest.mark.parametrize("code", SOURCES)
@pytest.mark.parametrize("token_types", ALL_TOKEN_TYPE_PERMUTATIONS)
def test_filter(code, token_types):
    _assert_counts_match(code, cslug.c_parse.filter(code, token_types),
                         token_types)


types_to_ctypes = [
    i.split(";") for i in """
int; c_int
char; c_char
float; c_float
double; c_double
short int; c_short
unsigned int; c_uint
long int; c_long
long long int; c_longlong
unsigned long; c_ulong
unsigned long long int; c_ulonglong
signed char; c_char
long double; c_longdouble
int32_t; c_int32
size_t; c_size_t
ssize_t; c_ssize_t
""".strip("\n").split("\n")
]

# unsigned char; c_uchar

aliases = [(i.split(","), j.strip()) for (i, j) in [
    i.split(";") for i in """
short, short int, signed short, signed short int; c_short
unsigned short, unsigned short int; c_ushort
int, signed, signed int; c_int
unsigned, unsigned int; c_uint
long, long int, signed long, signed long int; c_long
unsigned long, unsigned long int; c_ulong
long long, long long int, signed long long, signed long long int; c_longlong
unsigned long long, unsigned long long int; c_ulonglong
""".strip("\n").split("\n")
]]


@pytest.mark.parametrize(("source", "target"), types_to_ctypes)
def test_parse_type_name(source, target):
    assert cslug.c_parse.parse_parameter(source)[0] == target.strip()


@pytest.mark.parametrize(("sources", "target"), aliases)
def test_parse_type_name_aliases(sources, target):
    parsed = map(cslug.c_parse.parse_parameter, sources)
    a = next(parsed)
    assert a[0] == target
    for b in parsed:
        assert a == b


def test_gobbledegook():
    function = "int incomprehensible(;, float x);"
    with pytest.raises(ValueError, match=re.escape(function)):
        cslug.c_parse.parse_function(function)
