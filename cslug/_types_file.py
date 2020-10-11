# -*- coding: utf-8 -*-
"""
"""

import os, sys
import io
from pathlib import Path
import json
import ctypes

from cslug.c_parse import extract_prototypes, parse_prototype
from cslug import misc


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
        types = {}
        for source in self.sources:
            prototypes = extract_prototypes(misc.read(source)[0])
            for func in prototypes:
                name, *args = parse_prototype(func)
                types[name] = args
        return types

    def _types_from_json(self):
        return json.loads(misc.read(self.json_path)[0])

    def write(self, path=sys.stdout):
        misc.write(path, json.dumps(self.types, indent="  "), "\n")

    def apply(self, dll):
        """

        :param dll:
        :type dll: :class:`ctypes.CDLL`
        """

        for (name, (return_type, arg_types)) in self.types.items():
            func = getattr(dll, name)
            func.restype = getattr(ctypes, return_type, None)
            func.argtypes = [getattr(ctypes, i) for i in arg_types]


if __name__ == "__main__":
    pass
