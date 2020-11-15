# -*- coding: utf-8 -*-
"""
=============
cslug.c_parse
=============

The :mod:`c_parse` submodule provides some very bare-bones C parsing tools.

This module's sole purpose is to extract function and struct declarations to
generate prototypes in automatically generated header files, and to parse
type information from the declarations to be passed to :class:`Types`.

For a proper C parser, use `pycparser`_.

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


# Matches a function declaration such as ``void foo(int x)``
_function_re = _re.compile(r"""
# Return type:
(\w+) # initial type word.
(?=[ *]) # Non-consuming space or a * to split 1st type from whatever's next
[\w* ]+ # more type words or * symbols (or at least a space)
# Function name:
\w+
# Possible whitespace:
\s*
# Parameters. Lazily, just look for brackets. Detailed subparsing happens later.
\([^=;+)]*\)
""", flags=_re.MULTILINE | _re.VERBOSE) # yapf: disable


def search_function_declarations(text):
    text = filter(text, TokenType.CODE)
    for match in _function_re.finditer(text):

        if match.group(1) == "else":
            continue

        # Search for a following `{` to be sure this isn't just a prototype.
        # This should be combinable into the ``_function_re`` regex but it
        # causes it to become indefinitely slow so we stick to old-school
        # checking in Python.
        if _re.match(r"\s*{", text[match.end():]):
            yield match.group()


# Matches the same as ``_function_re`` but splits a prototype into a return
# type/name and a separate type/name for each parameter.
_parameter_re = _re.compile(r"([^(]*)\(([^)]*)\)\s*")


def parse_function_declaration(string):
    """Parse a function declaration into its name, its return type and its
    arguments."""
    res, args = _parameter_re.fullmatch(string).groups()
    args = list(_filter(None, _re.split(r"\s*,\s*", args)))
    args = [i for i in args if not _re.fullmatch(r"\s*void\s*", i)]
    a, b, name = parse_parameter(res)
    res = _choose_ctype(a, b, name)
    args = [_choose_ctype(*parse_parameter(i)) for i in args]
    return name, res, args


# --- Some weird Windows-only typedefs ---

_ALIAS_TYPES = {
    "SIZE_T": "size_t",
    "WORD": "int16_t",
    "DWORD": "int32_t",
    "QWORD": "int64_t",
}

_ALIAS_PTR_TYPES = {
    "LPSTR": "char",
    "LPCSTR": "char",
    "LPVOID": "void",
}


def parse_parameter(string):
    """Parse a variable or parameter declaration such as ``int * foo``.

    :param string: Declaration to parse.
    :type string: str
    :return: ``(ctypes_type_name, is_pointer, name)``
    :rtype: tuple[str, str, str]

    """
    pointer = 0
    type_words = []
    name = None
    for word in _re.findall(r"\w+", string):

        # Check for aliases.
        if word in _ALIAS_TYPES:
            word = _ALIAS_TYPES[word]

        # Check for aliased pointer types.
        if word in _ALIAS_PTR_TYPES:
            word = _ALIAS_PTR_TYPES[word]
            pointer += 1

        if word == "unsigned":
            type_words.append("u")
            # All unsigned types are prefixed with "u" in ctypes.
            continue

        if word == "signed":
            # Signed is a default anyway and ctypes never uses it.
            continue

        if word.endswith("_t") and not _re.fullmatch("s?size_t", word):
            # Exact types (e.g. int32_t) have the _t suffix removed in ctypes.
            # Except for size_t and ssize_t.
            word = word[:-2]

        if word == "int":
            # Int is particularly awkward in that it's optional and a default.
            # Just ignore it here. We'll add it on at the end later if it turns
            # out we need it.
            continue

        if word == "void":
            type_words.append("void")
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

    # Count how many *s or []s there are so check how many pointer layers deep.
    pointer += len(_re.findall(r"  \*  |  \[ [^]]* ]  ", string, _re.VERBOSE))

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

    if type is None and not pointer and "void" not in type_words:
        from warnings import warn
        from cslug.exceptions import TypeParseWarning
        warn("Unrecognised type '{}'. Type will not be set in wrapped C "
             "functions.".format(string), TypeParseWarning) # yapf: disable

    if type is None:
        # str None is less ugly to serialise.
        type = "None"

    return type, pointer, name


def _choose_ctype(type, pointer, word):
    if pointer:
        return _ctypes.c_void_p.__name__
    return type if type is not None else "None"


_struct_re = _re.compile(r"\s*typedef\s+struct(?:\s+\w+)?\s*"
                         r"{([^}]*)}\s*(\w+)\s*;")


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
