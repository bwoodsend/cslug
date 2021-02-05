# -*- coding: utf-8 -*-
"""
====================
:mod:`cslug.c_parse`
====================

The :mod:`cslug.c_parse` submodule provides some very bare-bones C parsing
tools.

This module's sole purpose is to extract function and struct declarations to
generate prototypes in automatically generated header files, and to parse
type information from the declarations to be passed to :class:`cslug.Types`.

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


RESERVED = {
    "if", "else", "switch", "case", "default", "break", "for", "while", "do",
    "goto", "return", "continue", "enum"
}

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
\([^=;+{]*\)
# Either a ; for a prototype or a { for a true definition.
(?=\s*([;{]))
""", flags=_re.MULTILINE | _re.VERBOSE) # yapf: disable


def search_functions(text, definitions=True, prototypes=False):
    text = filter(text, TokenType.CODE)
    for match in _function_re.finditer(text):

        if match.group(1) in RESERVED:
            continue

        if definitions and match.group(2) == "{":
            yield match.group()
        if prototypes and match.group(2) == ";":
            yield match.group()


# Matches the same as ``_function_re`` but splits a prototype into a return
# type/name and a separate type/name for each parameter.
_parameter_re = _re.compile(r"([^(]*)\(([^)]*)\)\s*")


def parse_function(string, typedefs=None):
    """Parse a function declaration into its name, its return type and its
    arguments."""
    try:
        res, args = _parameter_re.fullmatch(string).groups()
    except AttributeError:
        raise ValueError("Function '{}' not understood.".format(string))
    args = list(_filter(None, _re.split(r"\s*,\s*", args)))
    args = [i for i in args if not _re.fullmatch(r"\s*void\s*", i)]
    a, b, name = parse_parameter(res, typedefs=typedefs)
    res = _choose_ctype(a, b, name)
    args = [_choose_ctype(*parse_parameter(i, typedefs=typedefs)) for i in args]
    return name, res, args


def parse_functions(text, typedefs=None, definitions=True, prototypes=False):
    for func in search_functions(text, definitions=definitions,
                                 prototypes=prototypes):
        name, *args = parse_function(func, typedefs=typedefs)
        yield name, args


# --- Some weird Windows-only typedefs ---

# On second thought, there are 100s of these. I'm not adding them all...
# https://docs.microsoft.com/en-us/windows/win32/winprog/windows-data-types

_ALIAS_TYPES = {
    "SIZE_T": "size_t",
    "WORD": "int16_t",
    "DWORD": "int32_t",
    "QWORD": "int64_t",
    "ptrdiff_t": "ssize_t",
}

_ALIAS_PTR_TYPES = {
    "LPSTR": "char",
    "LPCSTR": "char",
    "LPVOID": "void",
}


def parse_parameter(string, typedefs=None):
    """Parse a variable or parameter declaration such as ``int * foo``.

    :param string: Declaration to parse.
    :type string: str
    :param typedefs:
    :return: ``(ctypes_type_name, pointers, name)``
    :rtype: tuple[str, int, str]

    The **pointers** output is a count of how many layers of pointer referencing
    cover the raw value. i.e. How many ``*``\\ s or ``[]``\\ s.

    """
    pointer = 0
    type_words = []
    name = None
    for word in _re.findall(r"\w+", string):

        # Check for user-defined types (without evaluating them).
        if typedefs and word in typedefs:
            type_words.append(word)

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

    if len(type_words) == 1 and typedefs and type_words[0] in typedefs:
        type = type_words[0]
    elif type_words or "signed" in string or "int" in string:
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
        warn("Unrecognised type '{}'. Type will default to void pointer."
             .format(string), TypeParseWarning) # yapf: disable
        type = "c_void_p"

    if type is None:
        # str None is less ugly to serialise.
        type = "None"

    return type, pointer, name


def _choose_ctype(type, pointer, word):
    """
    Select a ctypes type to assign a function parameter or return type.

    :return: An attribute name of ctypes_ or "None" (as a string).
    :restype: str

    """
    if pointer:
        # String types have a special pointer types ``c_char_p`` and
        # ``c_wchar_p`` for bytes and strings respectively. If ``type`` is
        # either ``c_char`` or ``c_wchar`` then use the appropriate pointer
        # type, but only if this is a direct pointer - not a pointer to a
        # pointer. Hence the ``pointer == 1`` below.
        if pointer == 1:
            _type = type + "_p"
            if hasattr(_ctypes, _type):
                return _type

        # ctypes does allow construction of arbitrary pointer classes e.g.
        # ``ctypes.POINTER(ctypes.c_int)`` but unlike the special ones for
        # strings they don't add any kind of functionality or type safety. So
        # for simplicity, just use anonymous void pointer.
        return _ctypes.c_void_p.__name__

    # If ``pointer`` is 0 then just return ``type``, converting any ``None``s
    # to strings.
    return type if type is not None else "None"


_struct_re = _re.compile(r"\s*typedef\s+struct(?:\s+\w+)?\s*"
                         r"{([^}]*)}\s*(\w+)\s*;")


def parse_struct(text):
    """

    :param text:
    :return:
    """
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
    """
    Search for and parse C Structure definitions in a block of text.

    :param text:
    :return: Iterable of (name, parameters) pairs as given by
             :meth:`parse_struct`.

    """
    return (parse_struct(i.group(0)) for i in _struct_re.finditer(text))
