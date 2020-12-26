# -*- coding: utf-8 -*-
"""
"""

from stdlib.parse import functions, Function


def cdef(f: Function):
    if f.index:
        out = f".. _`stdlib-{f.name}`:\n\n"
    else:
        out = ""
    return out + f"| :c:`{f.prototype}`\n|" \
                 f"    {f.description.replace('*', '**')}\n\n"


def cdef_library(name, contents):
    lines = [f"----\n\n{name}\n"]
    lines += [len(lines[0]) * "-" + "\n\n"]
    lines += [f"Functions defined with :c:`#include <{name}>`.\n\n"]
    lines += [cdef(i) for i in contents]
    return lines


title = [
    """\
.. This file is computer-generated. Edit stdlib/docs.py instead of this file.

=============================
Access the C Standard Library
=============================

.. automodule:: cslug.stdlib

-------

The functions on this page are grouped by the header file they are included
from.

"""
]

lines = sum([cdef_library(i, functions[i]) for i in sorted(functions)], title)

epilog = "".join(lines)
