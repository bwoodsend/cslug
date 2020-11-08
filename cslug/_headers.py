# -*- coding: utf-8 -*-
"""
"""

import sys
from pathlib import Path
import collections
import io
from enum import EnumMeta

from cslug.c_parse import search_function_declarations
from cslug import misc


class Header(object):

    def __init__(self, path, *sources, includes=(), defines=()):
        # TODO: Add support for io buffers.
        self.path = Path(path)
        if len(sources) == 0 and self.path.suffix != ".h":
            sources = (self.path,)
            self.path = self.path.with_suffix(".h")
        self.includes = misc.flatten(includes, types=(tuple, list))
        self.functions = collections.defaultdict(list)
        self.sources = [Path(i) for i in sources]
        self.defines = misc.flatten(defines, types=(tuple, list))
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
            "// -*- coding: utf-8 -*-\n",
            "// Header file generated automatically by cslug.\n",
            "// Do not modify this file directly as your changes will be "
            "overwritten.\n\n", "#ifndef HEADER_H\n#define HEADER_H\n\n"
        ]

        if self.includes:
            [lines.append("#include %s\n" % i) for i in self.includes]
            lines.append("\n")

        for defines in self.defines:
            if isinstance(defines, EnumMeta):
                lines.append("// {}\n".format(defines.__name__))
                defines = defines.__members__
            else:
                lines.append("// Definitions\n")
            for (key, val) in defines.items():
                val = getattr(val, "value", val)
                lines.append("#define {} {}\n".format(key, val))
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
