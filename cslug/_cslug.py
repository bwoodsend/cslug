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
from typing import List, Any, Union

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
        self._name_ = path
        self._path_ = path.with_name(path.stem + SUFFIX)
        _slug_refs[self._path_].append(weakref.ref(self))
        if len(sources) == 0 and path.suffix == ".c":
            sources = (path,)
        self._sources_ = [misc.as_path_or_readable_buffer(i) for i in sources]
        self._headers_ = misc.flatten(headers)
        for h in self._headers_:
            if not isinstance(h, Header):
                raise TypeError(
                    "The `headers` argument must be of `cslug.Header()` type, "
                    "not {}.".format(type(h)))
        self._type_map_ = Types(path.with_suffix(".json"), *self._sources_)
        self.__dll_ = None

    def _compile_(self):
        self._close_()

        command, buffers = self._compile_command_()
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
                raise exceptions.LibraryOpenElsewhereError(self._path_)
            raise exceptions.BuildError(command, msg)

        if msg:
            # Propagate any compiler warnings.
            warnings.warn(msg, category=exceptions.BuildWarning)
        return True

    def _close_(self, all=True):
        if all:
            new = []
            for slug in _slug_refs[self._path_]:
                # Close any other CSlugs that use the same DLL. This prevents a
                # lot of PermissionErrors or seg-faults if the user create a
                # CSlug twice (usually whilst console-bashing).
                if slug() is not None:
                    slug()._close_(all=False)
                    new.append(slug)
            _slug_refs[self._path_] = new
            return
        if self.__dll_ is not None:
            dlclose(ctypes.c_void_p(self.__dll_._handle))
            self.__dll_ = None

    @property
    def _dll_(self):
        if self.__dll_ is None:
            path = str(self._path_)
            if not self._path_.is_absolute():
                path = os.path.join(".", str(path))
            if not (self._path_.exists() and self._type_map_.json_path.exists()):
                self._make_()
            dll = ctypes.CDLL(path)
            self._type_map_.init_from_json()
            self._type_map_.apply(dll)
            self.__dll_ = dll
        return self.__dll_

    def _make_(self):
        self._close_()
        for header in self._headers_:
            header.make()
        ok = self._compile_()
        self._type_map_.make()
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
                self._close_()
            except:
                pass

    def _compile_command_(self, _cc=None):
        """Gets the _compile_ command invoked by :meth:`_compile_`."""
        _cc = cc(_cc)
        cc_name, version = cc_version(_cc)

        # Output filename
        output = ["-o", str(self._path_)]

        # Create a library, exporting all symbols.
        flags = [
            "-shared", "-rdynamic" if cc_name in ("tcc", "pcc") else "-fPIC"
        ]

        if cc_name == "gcc" and version >= (4, 6, 0):  # pragma: no cover
            # Optimize for speed.
            flags.append("-Ofast")

        # Compile for older versions of macOS.
        if cc_name in ("gcc", "clang") and OS == "Darwin":  # pragma: no cover
            flags += [f"-mmacosx-version-min={os.environ.get('MIN_OSX', 10.5)}"]

        # Set 32/64 bit.
        flags += ["-m" + str(BIT_NESS)]

        # Super noisy build warnings.
        warning_flags = "-Wall -Wextra".split()

        # Compile all .c files into 1 combined library.
        # Note that you don't pass header files to compilers.
        true_files = [str(i) for i in self._sources_ if isinstance(i, Path)]
        buffers = [i for i in self._sources_ if not isinstance(i, Path)]

        stdin_flags = "-x c -".split() if buffers else []

        return ([_cc] + output + flags + warning_flags + true_files +
                stdin_flags, buffers)

    def _check_printfs(self):
        return any(check_printfs(*misc.read(i)) for i in self._sources_)


# Create a global register of CSlugs grouped by DLL filename. This will be used
# by CSlug._close_(all=True)
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
