# -*- coding: utf-8 -*-
"""
"""

import ctypes
from textwrap import TextWrapper


def make_struct(name, fields):
    return type(
        name, (ctypes.Structure,), {
            "_fields_": fields,
            "__repr__": struct_repr,
            "_ptr": property(ctypes.addressof)
        })


def struct_repr(self):
    """

    :type self: ctypes.Structure
    """
    params = [
        "{}={}".format(i[0], repr(getattr(self, i[0]))) for i in self._fields_
    ]

    chunks = []
    for param in params[:-1]:
        chunks.append(param)
        chunks.append(",")
        chunks.append(" ")
    if params:
        chunks.append(params[-1])
    chunks.append(")")

    name = type(self).__name__

    wrapper = TextWrapper(initial_indent=name + "(",
                          subsequent_indent=" " * (len(name) + 1))

    lines = wrapper._wrap_chunks(chunks)
    if len(lines) > 1:
        return "\n".join(lines) + "\n"
    return lines[0]
