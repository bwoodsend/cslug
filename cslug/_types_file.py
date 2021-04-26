# -*- coding: utf-8 -*-
"""
"""

import os, sys
import io
from pathlib import Path
import json
import ctypes
import itertools
from typing import Union, Dict, List

from cslug.c_parse import parse_functions, parse_structs
from cslug import misc
from cslug._struct import make_struct


class Types(object):
    """Manages type information which is not found in a |../shared library|.

    * Scans source code for:

      - The name, argument and return types of each function.
      - The name, field names, types and bit-field sizes of structures.

    * Stores the above in a portable and quickly deserializable json file.
    * Sets the types for the contents of a :class:`ctypes.CDLL`.

    """
    def __init__(self, path, *sources, headers=(), compact=True):
        """

        Args:
            path (str or os.PathLike or io.TextIOBase):
                A filename to read or write serialised type information to.
            *sources (str or os.PathLike or io.TextIOBase):
                C sources to extract function definitions from.
            headers (str or os.PathLike or io.TextIOBase or list):
                C sources to extract function prototypes from.
            compact (bool):
                If true, serialise minimising file size. Otherwise, pretty
                format for human readability.

        Note the distinction between **sources** and **headers**.
        A function prototype such as :c:`int foo();` will be ignored if
        found in **sources** but included if it were in **headers**.
        A true function definition such as :c:`int foo() {}`, as well as
        structure definitions would be collected in either case.

        """
        self.sources = [misc.as_path_or_buffer(i) for i in sources]
        self.headers = list(map(misc.as_path_or_buffer, misc.flatten(headers)))
        self.json_path = misc.as_path_or_buffer(path)
        self.compact = compact

    types: dict
    """All type information collected. This is broken out into :attr:`functions`
    and :attr:`structs`.

    Note that this attribute is not set automatically. You must explicitly call
    either :meth:`init_from_source` or :meth:`init_from_json` before accessing.
    """

    json_path: Union[io.TextIOBase, Path]
    """File to read or write the json."""

    def init_from_source(self):
        """Initialise :attr:`types` by scanning source code."""
        self.types = self._types_from_source()

    def init_from_json(self):
        """Initialise :attr:`types` by  source code."""
        self.types = self._types_from_json()

    def _types_from_source(self):
        """Read and parse all source files.

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
        """Initialise from source then write to file."""
        self.init_from_source()
        self.write(self.json_path)

    def write(self, path=sys.stdout):
        """Serialise contents to **path**.

        Args:
            path (str or os.PathLike or io.TextIOBase):
                A filename or stream to write to. Defaults to
                :data:`sys.stdout`.

        """
        if self.compact:
            # Squeeze out redundant whitespace characters.
            out = json.dumps(self.types, separators=(",", ":")),
        else:
            # Write a git friendly, human readable json.
            out = json.dumps(self.types, indent="  ", sort_keys=True), "\n"
        misc.write(path, *out)

    # def __getattribute__(self, item):
    #     if item == "types":
    #         self.init()
    #     return super().__getattribute__(item)

    @property
    def functions(self) -> dict:
        """All functions (from true definitions of prototypes).

        The format is::

            function_name: [return_type, [arg_type, arg_type, ...]]

        All types are strings - either names of structures or attribute names of
        :mod:`ctypes`.

        """
        return self.types["functions"]

    @property
    def structs(self) -> dict:
        """All structures defined using :c:`typedef struct {...} name`.

        The format is::

            name: [(field_name, field_type), ...]

        Or for bit-field structs::

            name: [(field_name, field_type, bit_length), ...]

        """
        return self.types["structs"]

    def apply(self, dll, strict=False):
        """Set the type information for the contents of **dll**.

        Args:
            dll (ctypes.CDLL):
                The opened |../shared library| to apply type information to.
            strict (bool):
                Raise an :class:`AttributeError` if a symbol wasn't found.

        For every structure in ``self.structs``, turn it into a
        :class:`ctypes.Structure` and set it as an attribute of **dll**.
        For every function in ``self.functions``, get it from **dll**
        then set its ``argtypes`` and ``restype`` attributes.

        .. note::

            Structures don't normally go in |../shared libraries| but |cslug| lobs
            them in there for simplicity.

        """
        dll.__dict__.update(self._merge_apply(dll, strict=strict))

    def _merge_apply(self, *dlls, strict=False):
        structs = {}
        if strict:
            errors = []

        for (name, params) in self.structs.items():
            fields = [(name, getattr(ctypes, type), *bits)
                      for (name, type, *bits) in params]
            structs[name] = make_struct(name, fields)

        namespace = {}

        for (name, (return_type, arg_types)) in self.functions.items():
            for dll in dlls:
                func = getattr(dll, name, None)
                if func is not None:
                    break
            else:
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

            namespace[name] = func

        if strict and len(errors):
            dll = " ".join(map(repr, dlls))
            raise AttributeError(f"Symbols {errors} not found in {dll}.")

        namespace.update(structs)
        return namespace


if __name__ == "__main__":
    pass
