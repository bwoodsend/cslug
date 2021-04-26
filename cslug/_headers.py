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
    """Automatically generate a header file.

    For every function in every source file, generate a prototype for it.
    Use to automate the unfortunate copy/pasting required for multiple source
    files to interact with each other.

    Using a header like this globalises every function. Whilst this type of
    namespace collapsing would normally be discouraged, a shared library does
    not allow naming collisions anyway so there is little to no advantage in
    keeping namespaces separate.

    """
    def __init__(self, path, *sources, includes=(), defines=()):
        """

        Args:
            path: A file to write the header to.
            *sources: C source files to extract functions from.
            includes (str or list[str]): Other headers to :c:`#include`.
            defines (dict or enum.Enum or list[dict or enum.Enum]):
                Constants classes to :c:`#define`.

        For local **includes** wrap in double quotes :py:`includes='"header.h"'`
        or leave as is :py:`includes='header.h'`. For library includes use angle
        brackets :py:`includes='<stdint.h>'`.

        """
        self.path = Path(path)
        if len(sources) == 0 and self.path.suffix != ".h":
            sources = (self.path,)
            self.path = self.path.with_suffix(".h")
        self.includes = misc.flatten(includes)

        self.sources = [misc.as_path_or_buffer(i) for i in sources]
        self.defines = misc.flatten(defines)
        assert self.path.suffix == ".h"

    def _functions(self):
        functions = collections.defaultdict(list)
        for source in self.sources:
            code, name = misc.read(source)
            name = "<string>" if name is None else name.name
            functions[name] += search_functions(code)
        return functions

    def _generate(self):
        lines = [
            "// -*- coding: utf-8 -*-\n",
            "// Header file generated automatically by cslug.\n",
            "// Do not modify this file directly as your changes will be "
            "overwritten.\n\n",
        ]

        guard = re.sub(r"\W", "_", self.path.name.upper())
        lines += ["#ifndef {}\n".format(guard), "#define {}\n\n".format(guard)]

        if self.includes:
            for i in self.includes:
                lines.append(f"#include {_include_local_or_system(i)}\n")
            lines.append("\n")

        for defines in self.defines:
            if isinstance(defines, EnumMeta):
                lines.append("// {}\n".format(defines.__name__))
                defines = defines.__members__
            else:
                lines.append("// Definitions\n")
            for (key, val) in defines.items():
                # Get `val.value` if val is an enum.IntEnum.
                val = getattr(val, "value", val)
                lines.append("#define {} {}\n".format(key, val))
            lines.append("\n")

        for (name, funcs) in self._functions().items():
            lines.append("// " + name + "\n")
            lines.extend(i + ";\n" for i in funcs)
            lines.append("\n")

        lines.append("#endif\n")
        return lines

    def write(self, path=sys.stdout):
        """Reread sources and write to a file or stream."""
        if isinstance(path, io.IOBase):
            path.writelines(self._generate())
        else:
            with open(str(path), "w") as f:
                f.writelines(self._generate())

    def make(self):
        """Reread sources and write to :py:`self.path`."""
        self.write(self.path)


def _include_local_or_system(x):
    """Wrap **x** in quotes if it is not wrapped in angle brackets."""
    if re.fullmatch("<.*>", x):
        return x
    return '"' + x.strip('"') + '"'
