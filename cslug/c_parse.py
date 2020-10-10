# -*- coding: utf-8 -*-
"""
=============
cslug.c_parse
=============

The :mod:`c_parse` submodule provides some very bare-bones C parsing tools.

This module's sole purposes are to extract function prototypes to be used in
automatically generated header files. And to parse type information from those
prototypes.

"""

import re as _re
import ctypes as _ctypes
import enum as _enum
from builtins import filter as _filter


class TokenType(_enum.IntFlag):
    COMMENT = 1
    LITERAL = 2
    CODE = 4


def lex(text):
    deliminators = {
        "//": ("\n", TokenType.COMMENT),
        "/*": ("*/", TokenType.COMMENT),
        "\"": ("\"", TokenType.LITERAL),
        "'": ("'", TokenType.LITERAL)
    }

    blocks = []
    itr = iter(range(len(text)))

    start = 0
    for i in itr:
        for deliminator, (end, group) in deliminators.items():
            if text[i:i + len(deliminator)] == deliminator:
                blocks.append((start, i, TokenType.CODE))
                for j in itr:
                    if text[j:j + len(end)] == end:
                        break
                    if group is TokenType.LITERAL and text[j] == "\\":
                        next(itr)
                end = j + len(end)
                blocks.append((i, end, group))
                start = end
    blocks.append((start, len(text), TokenType.CODE))

    return blocks


def filter(text, token_types):
    keep = []

    for (start, end, group) in lex(text):
        if group & token_types:
            keep.append(text[start:end])
        else:
            keep.append("\n" * text[start:end].count("\n"))

    return "".join(keep)


# Matches a function prototype or declaration e.g. ``void foo(int x)``
_prototype_re = _re.compile(r"\w+(?:(?: +)|(?: *\* *))\w+\([\w*&\s,]*\)",
                            flags=_re.MULTILINE)


def extract_prototypes(text):
    return _prototype_re.findall(filter(text, TokenType.CODE))


# Matches the same as ``_prototype_re`` but splits a prototype into a return
# type/name and a separate type/name for each parameter.
_prototype_type_name_re = _re.compile(r"([^(]*)\(([^)]*)\)\s*")


def parse_prototype(string):
    """Parse a function prototype."""
    res, args = _prototype_type_name_re.fullmatch(string).groups()
    args = list(_filter(None, _re.split(r"\s*,\s*", args)))
    args = [i for i in args if not _re.fullmatch(r"\s*void\s*", i)]
    a, b, name = _parse_type_name(res)
    res = _choose_ctype(a, b, name)
    args = [_choose_ctype(*_parse_type_name(i)) for i in args]
    return name, res, args


def _parse_type_name(string):
    pointer = False
    type = None
    prefix = ""
    for word in _re.findall(r"\w+|[*&]", string):
        if word.endswith("_t"):
            word = word[:-2]
        if word == "unsigned":
            prefix = "u"
        if _re.fullmatch(r"\*+", word):
            pointer = True
        type = type or getattr(_ctypes, "c_" + prefix + word, None)
    return type, pointer, word


def _choose_ctype(type, pointer, word):
    ctype = _ctypes.c_void_p if pointer else type
    return ctype.__name__ if ctype is not None else "None"
