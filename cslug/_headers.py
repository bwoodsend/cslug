# -*- coding: utf-8 -*-
"""
"""

import sys
from pathlib import Path
import collections
import io
from enum import Enum

from cslug.c_parse import search_function_declarations


class Header(object):

    def __init__(self, path, *sources, includes=(), defines=()):
        self.path = Path(path)
        if len(sources) == 0 and self.path.suffix != ".h":
            sources = (self.path,)
            self.path = self.path.with_suffix(".h")
        self.includes = includes
        self.functions = collections.defaultdict(list)
        self.sources = [Path(i) for i in sources]
        self.defines = defines
        assert self.path.suffix == ".h"
        assert all(i.suffix != ".h" for i in self.sources)
        if all(map(Path.exists, self.sources)):
            [self.add_source(i) for i in self.sources]
            self.write(self.path)

    def add_source(self, source):
        source = Path(source)
        self.functions[source] += search_function_declarations(
            source.read_text("utf-8"))

    def generate(self):
        lines = [
            "// Header file generated automatically by cslug.\n",
            "// It is unadvisable to modify this file directly.\n\n",
            "#ifndef HEADER_H\n#define HEADER_H\n\n"
        ]

        [lines.append("#include %s\n" % i) for i in self.includes]

        for defines in self.defines:
            if isinstance(self.defines, Enum):
                lines.append("// {}\n".format(defines.__name__))
                defines = defines.__members__
            else:
                lines.append("// Definitions\n")
            for i in defines.items():
                lines.append("#define {} {}\n".format(*i))
            lines.append("\n")

        for (path, funcs) in self.functions.items():
            lines.append("// " + path.name + "\n")
            lines.extend(i + ";\n" for i in funcs)
            lines.append("\n")

        lines.append("#endif\n")
        return lines

    def write(self, path=sys.stdout):
        if isinstance(path, io.IOBase):
            path.writelines(self.generate())
        else:
            with open(str(path), "w") as f:
                f.writelines(self.generate())
