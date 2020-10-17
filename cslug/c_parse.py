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
    a, b, name = parse_parameter(res)
    res = _choose_ctype(a, b, name)
    args = [_choose_ctype(*parse_parameter(i)) for i in args]
    return name, res, args


def parse_parameter(string):
    """Parse a variable or parameter declaration e.g. ``int * foo`` into

    :param string: Declaration to parse.
    :type string: str
    :return: ``(ctypes_type_name, is_pointer, name)``
    :rtype: tuple[str, bool, str]

    """
    # XXX: This logic is pretty hacky.
    pointer = False
    type_words = []
    name = None
    for word in _re.findall(r"\w+|[*&]", string):

        if word == "unsigned":
            type_words.append("u")
            # All unsigned types are prefixed with "u" in ctypes.
            continue

        if word == "signed":
            # Signed is a default anyway and ctypes never uses it.
            continue

        if _re.fullmatch(r"\*+", word):
            # Pointers to pointers (**) are to be treated as just pointers.
            pointer = True
            continue

        if word.endswith("_t") and word != "size_t":
            # Exact types (e.g. int32_t) have the _t suffix removed in ctypes.
            # Except for size_t.
            word = word[:-2]

        if word == "int":
            # Int is particularly awkward in that it's optional and a default.
            # Just ignore it here. We'll add it on at the end later if it turns
            # out we need it.
            continue

        if hasattr(_ctypes, "c_" + word):
            # To test if `word` is a type, check if it exists in ctypes. This
            # may not be the whole type too be returned if the type given is
            # multi-worded e.g. long double.
            type_words.append(word)
        else:
            # Otherwise assume this is the parameter name. This will get
            # confused by custom types but I don't see how to avoid that without
            # some much heavier parsing of the rest of the file.
            name = word

    if type_words or "signed" in string or "int" in string:
        type = "c_" + "".join(type_words)
        # Check if type is a valid ctype:
        if not hasattr(_ctypes, type):
            # If not, append `int` and try again:
            type += "int"
            if not hasattr(_ctypes, type):
                # Presumably this is a custom type. Or unsupported by ctypes.
                type = None
    else:
        type = None

    if type is None:
        from warnings import warn
        from cslug.exceptions import TypeParseWarning
        warn("Unrecognised type '{}'. Type will not be set in wrapped C "
             "functions.".format(string), TypeParseWarning) # yapf: disable
        # str None is less ugly to serialise.
        type = "None"

    return type, pointer, name


def _choose_ctype(type, pointer, word):
    if pointer:
        return _ctypes.c_void_p.__name__
    return type if type is not None else "None"


_struct_re = _re.compile(r"\s*typedef\s+struct(?:\s+\w+)?\s*"
                         r"\{([^\}]*)\}\s*(\w+)\s*;")


def parse_struct(text):
    params_str, name = _struct_re.match(text).groups()
    params = []
    param: str
    for param in params_str.split(";"):
        param = param.strip(" \n\t")
        if not param:
            continue
        colon = param.find(":")
        if colon != -1:
            bitfield_size = int(param[colon + 1:])
            param = param[:colon]
        else:
            bitfield_size = None
        type, pointer, param_name = parse_parameter(param)
        ctype = _choose_ctype(type, pointer, None)
        if bitfield_size is None:
            params.append((param_name, ctype))
        else:
            params.append((param_name, ctype, bitfield_size))

    return name, params


def parse_structs(text):
    return (parse_struct(i.group(0)) for i in _struct_re.finditer(text))
