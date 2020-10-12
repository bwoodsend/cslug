# -*- coding: utf-8 -*-
"""
"""

import os, sys
from pathlib import Path

import pytest

import cslug

pytestmark = pytest.mark.first

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
