# -*- coding: utf-8 -*-
"""
"""

import os, sys
import io
from pathlib import Path
import json
import ctypes
import itertools

from cslug.c_parse import parse_functions, parse_structs
from cslug import misc
from cslug._struct import make_struct


class Types(object):
    def __init__(self, path, *sources, headers=()):
        self.sources = [misc.as_path_or_buffer(i) for i in sources]
        self.headers = list(map(misc.as_path_or_buffer, misc.flatten(headers)))
        self.json_path = misc.as_path_or_buffer(path)

    def init_from_source(self):
        self.types = self._types_from_source()

    def init_from_json(self):
        self.types = self._types_from_json()

    def _types_from_source(self):
        """

        :rtype: dict
        """
        functions = {}
        structs = {}
        for source in itertools.chain(self.sources, self.headers):
            structs.update(parse_structs(misc.read(source)[0]))

        for source in self.sources:
            functions.update(
                parse_functions(misc.read(source)[0], typedefs=structs))
        for source in self.headers:
            functions.update(
                parse_functions(
                    misc.read(source)[0], typedefs=structs, prototypes=True))

        return {"functions": functions, "structs": structs}

    def _types_from_json(self):
        return json.loads(misc.read(self.json_path)[0])

    def make(self):
        self.init_from_source()
        self.write(self.json_path)

    def write(self, path=sys.stdout):
        misc.write(path, json.dumps(self.types, indent="  ", sort_keys=True),
                   "\n")

    # def __getattribute__(self, item):
    #     if item == "types":
    #         self.init()
    #     return super().__getattribute__(item)

    def apply(self, dll, strict=False):
        """Set the type information for the contents of **dll**.

        Args:
            dll (ctypes.CDLL):
                The opened |shared library| to apply type information to.
            strict (bool):
                Raise an :class:`AttributeError` if a symbol wasn't found.

        For every structure in ``self.types["structs"]``, turn it into a
        :class:`ctypes.Structure` and set it as an attribute of **dll**.
        For every function in ``self.types["functions"]``, get it from **dll**
        then set its ``argtypes`` and ``restype`` attributes.

        .. note::

            Structures don't normally go in |../shared libraries| but |cslug| lobs
            them in there for simplicity.

        """
        structs = {}
        if strict:
            errors = []

        for (name, params) in self.types["structs"].items():
            fields = [(name, getattr(ctypes, type), *bits)
                      for (name, type, *bits) in params]
            structs[name] = make_struct(name, fields)

        dll.__dict__.update(structs)

        for (name, (return_type, arg_types)) in self.types["functions"].items():
            func = getattr(dll, name, None)
            if func is None:
                # A function may be missing if any of:
                #
                #   - The function was declared `inline`.
                #   - The function was not `__dll_export`ed and the `--fPIC`
                #     build flag was not used.
                #   - CSlug screwed up (not that unlikely).
                #
                # Don't crash if this is the case.
                if strict:
                    errors.append(name)
                # The continue below gets ignored by coverage. Add this useless
                # statement to ensure it's being ran.
                else:
                    pass
                continue  # pragma: no cover

            # Set function return type. Default to no return value.
            func.restype = structs.get(return_type) \
                           or getattr(ctypes, return_type, None)

            # Set argument types. Default to int. If this is wrong however this
            # will almost certainly cause strange incorrect behaviour.
            func.argtypes = [
                structs.get(i) or getattr(ctypes, i, ctypes.c_int)
                for i in arg_types
            ]

        if strict and len(errors):
            raise AttributeError(f"Symbols {errors} not found in {dll}.")


if __name__ == "__main__":
    pass
