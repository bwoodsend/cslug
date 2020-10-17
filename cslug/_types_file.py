# -*- coding: utf-8 -*-
"""
"""

import os, sys
import io
from pathlib import Path
import json
import ctypes

from cslug.c_parse import extract_prototypes, parse_prototype, parse_structs
from cslug import misc
from cslug._struct import make_struct


class Types(object):

    def __init__(self, path, *sources):
        self.sources = [misc.as_path_or_buffer(i) for i in sources]
        self.json_path = misc.as_path_or_buffer(path)

        reload = (not misc.exists_or_buffer(self.json_path)) \
            or all(map(misc.exists_or_buffer, self.sources))

        if reload:
            self.types = self._types_from_source()
            self.write(self.json_path)
        else:
            self.types = self._types_from_json()

    def _types_from_source(self):
        """

        :rtype: dict
        """
        functions = {}
        structs = {}
        for source in self.sources:
            source = misc.read(source)[0]
            prototypes = extract_prototypes(source)
            for func in prototypes:
                name, *args = parse_prototype(func)
                functions[name] = args

            structs.update(parse_structs(source))

        return {"functions": functions, "structs": structs}

    def _types_from_json(self):
        return json.loads(misc.read(self.json_path)[0])

    def write(self, path=sys.stdout):
        misc.write(path, json.dumps(self.types, indent="  "), "\n")

    def apply(self, dll):
        """

        :param dll:
        :type dll: :class:`ctypes.CDLL`
        """

        for (name, (return_type, arg_types)) in self.types["functions"].items():
            func = getattr(dll, name)
            func.restype = getattr(ctypes, return_type, None)
            func.argtypes = [getattr(ctypes, i) for i in arg_types]

        for (name, params) in self.types["structs"].items():
            fields = [(name, getattr(ctypes, type), *bits)
                      for (name, type, *bits) in params]
            setattr(dll, name, make_struct(name, fields))


if __name__ == "__main__":
    pass
