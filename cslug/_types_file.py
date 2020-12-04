# -*- coding: utf-8 -*-
"""
"""

import os, sys
import io
from pathlib import Path
import json
import ctypes

from cslug.c_parse import search_function_declarations, parse_function_declaration, parse_structs
from cslug import misc
from cslug._struct import make_struct


class Types(object):
    def __init__(self, path, *sources):
        self.sources = [misc.as_path_or_buffer(i) for i in sources]
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
        for source in self.sources:
            structs.update(parse_structs(misc.read(source)[0]))

        for source in self.sources:
            for func in search_function_declarations(misc.read(source)[0]):
                name, *args = parse_function_declaration(func, typedefs=structs)
                functions[name] = args

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

    def apply(self, dll):
        """

        :param dll:
        :type dll: :class:`ctypes.CDLL`
        """
        structs = {}

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
                continue

            # Set function return type. Default to no return value.
            func.restype = structs.get(return_type) \
                           or getattr(ctypes, return_type, None)

            # Set argument types. Default to int. If this is wrong however this
            # will almost certainly cause strange incorrect behaviour.
            func.argtypes = [
                structs.get(i) or getattr(ctypes, i, ctypes.c_int)
                for i in arg_types
            ]


if __name__ == "__main__":
    pass
