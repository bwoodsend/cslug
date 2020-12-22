# -*- coding: utf-8 -*-
"""
"""

import sys
from pathlib import Path
import collections
import io
import re
from enum import EnumMeta

from cslug.c_parse import search_functions
from cslug import misc


class Header(object):
    def __init__(self, path, *sources, includes=(), defines=()):
        self.path = Path(path)
        if len(sources) == 0 and self.path.suffix != ".h":
            sources = (self.path,)
            self.path = self.path.with_suffix(".h")
        self.includes = misc.flatten(includes)

        self.sources = [misc.as_path_or_buffer(i) for i in sources]
        self.defines = misc.flatten(defines)
        assert self.path.suffix == ".h"

    def functions(self):
        functions = collections.defaultdict(list)
        for source in self.sources:
            code, name = misc.read(source)
            name = "<string>" if name is None else name.name
            functions[name] += search_functions(code)
        return functions

    def generate(self):
        lines = [
            "// -*- coding: utf-8 -*-\n",
            "// Header file generated automatically by cslug.\n",
            "// Do not modify this file directly as your changes will be "
            "overwritten.\n\n",
        ]

        guard = re.sub(r"\W", "_", self.path.name.upper())
        lines += ["#ifndef {}\n".format(guard), "#define {}\n\n".format(guard)]

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

        for (name, funcs) in self.functions().items():
            lines.append("// " + name + "\n")
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

    def make(self):
        self.write(self.path)
