# -*- coding: utf-8 -*-
"""
"""

import os
from pathlib import Path
import ctypes
from subprocess import Popen, PIPE
import re
import warnings
import platform

from cslug._types_file import Types
from cslug import misc

# TODO: maybe try utilising this. Probably not worth it...
# https://stackoverflow.com/questions/17942874/stdout-redirection-with-ctypes


class BuildError(Exception):

    def __str__(self):
        return "The build command:\n\n%s\n\nFailed with:\n\n%s\n" % self.args


class BuildWarning(Warning):
    pass


OS = platform.system()
SUFFIX = {"Windows": ".dll", "Linux": ".so", "Darwin": ".dylib"}.get(OS, ".so")

_ADDRESS_VIEW = ctypes.ARRAY(ctypes.c_void_p, 100)


class CSlug(object):

    def __init__(self, path, *sources):
        path = misc.as_path_or_buffer(path)
        if not isinstance(path, Path):
            raise TypeError("The path to a CSlug's DLL must be a true path, not"
                            "a {}.".format(type(path)))
        self.path = path.with_suffix(SUFFIX)
        if len(sources) == 0 and path.suffix == ".c":
            sources = (path,)
        self.sources = [misc.as_path_or_readable_buffer(i) for i in sources]
        self.types_dict = Types(self.path.with_suffix(".json"), *self.sources)
        self.types_dict.init_from_json()
        self._dll = None

    def compile(self):
        self.close()

        command, buffers = self.make_command()
        p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                  universal_newlines=True)
        for buffer in buffers:
            p.stdin.write(misc.read(buffer)[0])
        p.stdin.close()
        p.wait()
        msg = p.stderr.read()

        # If all just whitespace.
        if not re.search(r"\S", msg):
            msg = ""

        if p.returncode:
            raise BuildError(command, msg)
            return False

        if msg:
            # Propagate any gcc compile warnings.
            warnings.warn(msg, category=BuildWarning)
        return True

    def close(self):
        try:
            handle = self._dll._handle
            ctypes.windll.kernel32.FreeLibrary(handle)
        except (NameError, AttributeError):
            pass
        self._dll = None

    @property
    def dll(self):
        if self._dll is None:
            path = str(self.path)
            if not self.path.is_absolute():
                path = os.path.join(".", str(path))
            if not self.path.exists():
                self.make()
            self._dll = ctypes.CDLL(path)
            self.types_dict.apply(self._dll)
        return self._dll

    def make(self):
        self.close()
        # check_printfs()
        # make_header()
        # make_json_header()
        return self.compile()

    def __del__(self):
        self.close()

    def make_command(self):
        """Gets the compile command invoked by :meth:`call_gcc`."""

        # Output filename
        output = ["-o", str(self.path)]

        # Create a library, in a format Windows will accept, optimize for speed.
        flags = "-shared -fPIC -Ofast".split()

        # Compile for older versions of macOS.
        if OS == "Darwin":
            flags += ["-mmacosx-version-min=10.1"]

        # Super noisy build warnings.
        warning_flags = "-Wall -Wextra".split()

        # Compile all .c files into 1 combined library.
        # Note that you don't pass header files to gcc.
        true_files = [str(i) for i in self.sources if isinstance(i, Path)]
        buffers = [i for i in self.sources if not isinstance(i, Path)]

        stdin_flags = "-x c -".split() if buffers else []

        return (["gcc"] + output + flags + warning_flags + true_files +
                stdin_flags, buffers)


def ptr(bytes_like):
    """Get a ``ctypes.c_void_p`` to any Python object supporting the C buffer
    protocol. i.e. calling ``bytes(obj)`` doesn't raise a ``TypeError``.
    This includes bytes, memoryviews and numpy arrays. This intentionally
    doesn't inc-ref the buffer so don't let it be deleted in Python until C is
    done with it. i.e. ``c_method(ptr(b"buffer"))`` will likely crash Python.
    Instead use:

    .. code-block:: python

        buffer = b"buffer"
        c_method(ptr(buffer))

        # Now it is safe to delete the buffer (or leave Python's gc to do it
        # automatically as you normally would any other Python object).
        del buffer # optional

    """
    # I'm really not convinced by this.
    obj = ctypes.py_object(bytes_like)
    address = _ADDRESS_VIEW()
    ctypes.pythonapi.PyObject_GetBuffer(obj, address, 24)
    # The above inc-refs it which leads to memory leaks. We should call the
    # following after we're finished with the pointer to safely allow it to be
    # deleted but it's easier just to say always hang onto buffers in Python
    # until you're done with them.
    ctypes.pythonapi.PyBuffer_Release(address)

    # Alternatively, the following is clunkier but safer - maybe switch to this
    # in future, but it makes numpy as dependency.
    # np.frombuffer(bytes_like, dtype=np.uint8).ctypes.data
    return address[0]


def check_printfs(file=None, name=None):
    if file is None:
        return any(check_printfs(i) for i in HERE.glob("*.c"))
    if isinstance(file, Path):
        return check_printfs(file.read_text("utf-8"), name or file.name)

    file = _strip_comments(file)
    out = False
    # Can't use enumerate(file.split("\n")) here because of "# n" line number
    # changes.
    i = 0
    for line in file.split("\n"):
        match = re.search(r"# (\d+)", line)
        if match:
            i = int(match.group(1))
        if "printf" in line:
            # if "//" not in line or line.index("//") > line.index("printf"):
            warnings.warn("printf in {} on line {}".format(name or "?", i))
            out = True
        i += 1
    return out
