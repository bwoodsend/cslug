# -*- coding: utf-8 -*-
"""
"""

import os, sys
import io
from pathlib import Path
import json
import ctypes

from cslug.c_parse import extract_prototypes, parse_prototype


class Types(object):

    def __init__(self, path, *sources):
        self.sources = [Path(i) for i in sources]
        self.json_path = Path(path).with_suffix(".json")

        reload = (not self.json_path.exists()) \
                or all(map(Path.exists, self.sources))

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
            prototypes = extract_prototypes(source.read_text("utf-8"))
            for func in prototypes:
                name, *args = parse_prototype(func)
                types[name] = args
        return types

    def _types_from_json(self):
        with self.json_path.open("r") as f:
            return json.load(f)

    def write(self, path=sys.stdout):
        file = path if isinstance(path, io.TextIOBase) else open(str(path), "w")
        json.dump(self.types, file, indent="  ")
        file.write("\n")
        if file is not path:
            file.close()

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
