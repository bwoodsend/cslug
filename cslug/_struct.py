# -*- coding: utf-8 -*-
"""
"""

import ctypes
from pprint import pformat


def make_struct(name, fields):
    return type(name, (ctypes.Structure,), {
        "_fields_": fields,
        "__repr__": struct_repr
    })


def struct_repr(self):
    """

    :type self: ctypes.Structure
    """
    args = [
        "{}={}".format(i[0], repr(getattr(self, i[0]))) for i in self._fields_
    ]
    out = type(self).__name__ + "(" + ", ".join(args) + ")"
    if len(out) <= 70:
        return out
    out = type(self).__name__ + "("
    out += (",\n" + " " * len(out)).join(args) + ")"
    return out
