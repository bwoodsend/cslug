# -*- coding: utf-8 -*-
"""
"""

import os, sys
from pathlib import Path
import ctypes
from subprocess import Popen, PIPE, run
import re
import warnings
import platform
import collections
import weakref

from cslug._types_file import Types
from cslug import misc, exceptions, c_parse
from cslug._headers import Header
from cslug._cc import cc, cc_version
from cslug._stdlib import dlclose

# TODO: maybe try utilising this. Probably not worth it...
# https://stackoverflow.com/questions/17942874/stdout-redirection-with-ctypes

# Choose an appropriate DLL suffix. Asides from keeping files from different OSs
# or 64/32bits getting mixed up, it also gives Linux .so files invalid Python
# names which prevents Python from trying (and failing) to interpret a CSlug
# file as a Python extension module if a CSlug has the same name as a .py file.

OS = platform.system()
SUFFIX = {"Windows": ".dll", "Linux": ".so", "Darwin": ".dylib"}.get(OS, ".so")
BIT_NESS = 8 * ctypes.sizeof(ctypes.c_void_p)
SUFFIX = "-{}-{}bit{}".format(OS, BIT_NESS, SUFFIX)


class CSlug(object):
    def __init__(self, path, *sources, headers=()):
        path, *sources = misc.flatten(sources, initial=misc.flatten(path))
        path = misc.as_path_or_buffer(path)
        if not isinstance(path, Path):
            raise TypeError("The path to a CSlug's DLL must be a true path, not"
                            "a {}.".format(type(path)))
        self.name = path
        self.path = path.with_name(path.stem + SUFFIX)
        _slug_refs[self.path].append(weakref.ref(self))
        if len(sources) == 0 and path.suffix == ".c":
            sources = (path,)
        self.sources = [misc.as_path_or_readable_buffer(i) for i in sources]
        self.headers = misc.flatten(headers)
        for h in self.headers:
            if not isinstance(h, Header):
                raise TypeError(
                    "The `headers` argument must be of `cslug.Header()` type, "
                    "not {}.".format(type(h)))
        self.types_dict = Types(path.with_suffix(".json"), *self.sources)
        self._dll = None

    def compile(self):
        self.close()

        command, buffers = self.compile_command()
        p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                  universal_newlines=True)
        for buffer in buffers:
            p.stdin.write(misc.read(buffer)[0])
        p.stdin.close()
        p.wait()
        msg = p.stderr.read()
        p.stderr.close(), p.stdout.close()

        # If all just whitespace.
        if not re.search(r"\S", msg):
            msg = ""

        if p.returncode:
            if re.search("(?:open output|write).*permission denied", msg,
                         re.DOTALL | re.IGNORECASE):  # pragma: Windows
                raise exceptions.LibraryOpenElsewhereError(self.path)
            raise exceptions.BuildError(command, msg)

        if msg:
            # Propagate any compiler warnings.
            warnings.warn(msg, category=exceptions.BuildWarning)
        return True

    def close(self, all=True):
        if all:
            new = []
            for slug in _slug_refs[self.path]:
                # Close any other CSlugs that use the same DLL. This prevents a
                # lot of PermissionErrors or seg-faults if the user create a
                # CSlug twice (usually whilst console-bashing).
                if slug() is not None:
                    slug().close(all=False)
                    new.append(slug)
            _slug_refs[self.path] = new
            return
        if self._dll is not None:
            dlclose(ctypes.c_void_p(self._dll._handle))
            self._dll = None

    @property
    def dll(self):
        if self._dll is None:
            path = str(self.path)
            if not self.path.is_absolute():
                path = os.path.join(".", str(path))
            if not (self.path.exists() and self.types_dict.json_path.exists()):
                self.make()
            dll = ctypes.CDLL(path)
            self.types_dict.init_from_json()
            self.types_dict.apply(dll)
            self._dll = dll
        return self._dll

    def make(self):
        self.close()
        for header in self.headers:
            header.make()
        ok = self.compile()
        self.types_dict.make()
        self._check_printfs()
        return ok

    def __del__(self):
        # Release the DLL on deletion of this object on Windows so that make()
        # can be called without tripping permission errors.
        # At Python exit, the DLL may have been closed and deleted already. If
        # we try to re-close on Linux we get a seg-fault. On Windows we get
        # some kind of AttributeError or occasionally an OSError.
        if OS == "Windows" or sys.platform == "msys":  # pragma: Windows
            try:
                self.close()
            except:
                pass

    def compile_command(self, _cc=None):
        """Gets the compile command invoked by :meth:`compile`."""
        _cc = cc(_cc)
        cc_name, version = cc_version(_cc)

        # Output filename
        output = ["-o", str(self.path)]

        # Create a library, exporting all symbols.
        flags = [
            "-shared", "-rdynamic" if cc_name in ("tcc", "pcc") else "-fPIC"
        ]

        if cc_name == "gcc" and version >= (4, 6, 0):  # pragma: no cover
            # Optimize for speed.
            flags.append("-Ofast")

        # Compile for older versions of macOS.
        if cc_name == "gcc" and OS == "Darwin":  # pragma: Darwin
            flags += ["-mmacosx-version-min=10.5"]

        # Set 32/64 bit.
        flags += ["-m" + str(BIT_NESS)]

        # Super noisy build warnings.
        warning_flags = "-Wall -Wextra".split()

        # Compile all .c files into 1 combined library.
        # Note that you don't pass header files to compilers.
        true_files = [str(i) for i in self.sources if isinstance(i, Path)]
        buffers = [i for i in self.sources if not isinstance(i, Path)]

        stdin_flags = "-x c -".split() if buffers else []

        return ([_cc] + output + flags + warning_flags + true_files +
                stdin_flags, buffers)

    def _check_printfs(self):
        return any(check_printfs(*misc.read(i)) for i in self.sources)


# Create a global register of CSlugs grouped by DLL filename. This will be used
# by CSlug.close(all=True)
try:
    _slug_refs
except NameError:
    _slug_refs = collections.defaultdict(list)


def check_printfs(text, name=None):
    """Test and warn for ``printf()``\\ s in C code.

    :return: True is there were any found.
    """
    text = c_parse.filter(text, c_parse.TokenType.CODE)
    name = name or "<string>"
    out = False

    # We can't use enumerate(file.split("\n")) here because of "# n" line number
    # changes, otherwise this would be a lot less wordy.
    i = 0
    for line in text.split("\n"):

        match = re.search(r"# (\d+)", line)
        if match:
            i = int(match.group(1))

        if "printf" in line:
            warnings.warn(
                "printf() detected at \"{}:{}\". Note you will only see its "
                "output if running Python from shell. Otherwise it will slow "
                "you code down with no apparent cause.".format(name, i),
                category=exceptions.PrintfWarning,
            ) # yapf: disable
            out = True
        i += 1
    return out
