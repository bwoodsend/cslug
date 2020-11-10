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
import shutil

from cslug._types_file import Types
from cslug import misc, exceptions, c_parse

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

    def __init__(self, path, *sources):
        path, *sources = misc.flatten(sources, (tuple, list),
                                      initial=misc.flatten(path, (tuple, list)))
        path = misc.as_path_or_buffer(path)
        if not isinstance(path, Path):
            raise TypeError("The path to a CSlug's DLL must be a true path, not"
                            "a {}.".format(type(path)))
        self.path = path.with_name(path.stem + SUFFIX)
        if len(sources) == 0 and path.suffix == ".c":
            sources = (path,)
        self.sources = [misc.as_path_or_readable_buffer(i) for i in sources]
        self.types_dict = Types(path.with_suffix(".json"), *self.sources)
        self._dll = None

    def compile(self):
        self.close()
        if shutil.which("gcc") is None:
            raise exceptions.NoGccError

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
            raise exceptions.BuildError(command, msg)

        if msg:
            # Propagate any gcc compile warnings.
            warnings.warn(msg, category=exceptions.BuildWarning)
        return True

    def close(self):
        if self._dll is not None:
            free_dll_handle(ctypes.c_void_p(self._dll._handle))
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
        if OS == "Windows":  # pragma: no branch
            try:
                self.close()
            except:
                pass

    def make_command(self):
        """Gets the compile command invoked by :meth:`call_gcc`."""

        # Output filename
        output = ["-o", str(self.path)]

        # Create a library, in a format Windows will accept, optimize for speed.
        flags = "-shared -fPIC -Ofast".split()

        # Compile for older versions of macOS.
        if OS == "Darwin":  # pragma: no cover
            flags += ["-mmacosx-version-min=10.1"]

        # Set 32/64 bit.
        flags += ["-m" + str(BIT_NESS)]

        # Super noisy build warnings.
        warning_flags = "-Wall -Wextra".split()

        # Compile all .c files into 1 combined library.
        # Note that you don't pass header files to gcc.
        true_files = [str(i) for i in self.sources if isinstance(i, Path)]
        buffers = [i for i in self.sources if not isinstance(i, Path)]

        stdin_flags = "-x c -".split() if buffers else []

        return (["gcc"] + output + flags + warning_flags + true_files +
                stdin_flags, buffers)

    def _check_printfs(self):
        return any(check_printfs(*misc.read(i)) for i in self.sources)


def ptr(bytes_like):
    """Get a ``ctypes.c_void_p`` to any Python object supporting the C buffer
    protocol.

    A ``bytes_like`` object is anything that calling ``bytes(obj)`` doesn't
    raise a ``TypeError``. This includes bytes, memoryviews and numpy arrays.

    This intentionally doesn't inc-ref the buffer so don't let it be deleted in
    Python until C is done with it. i.e. ``c_method(ptr(b"buffer"))`` will
    likely crash Python. Instead use:

    .. code-block:: python

        buffer = b"buffer"
        c_method(ptr(buffer))

        # Now it is safe to delete the buffer (or leave Python's gc to do it
        # automatically as you normally would any other Python object).
        del buffer # optional

    If you are using `numpy`_ then you should be aware that this method only
    accepts C-contiguous buffers. If you understand how contiguity works and
    have explicitly supported non-contiguous buffers in your C code then you may
    use :meth:`nc_ptr` instead. Otherwise convert your arrays to contiguous ones
    using either::

        array = np.ascontiguousarray(array)

    or::

        array = np.asarray(array, order="C")

    """
    try:
        return _ptr(bytes_like, 0)
    # I'm not sure why the difference but depending on the input, you may get
    # either of these exception types from requesting a contiguous buffer from
    # a non-contiguous one.
    except (ValueError, BufferError) as ex:  # pragma: no branch
        if len(ex.args) == 1 and "not C-contiguous" in ex.args[0]:
            raise ValueError(
                ex.args[0] + " and, by using `ptr()`, you have specified that "
                "a contiguous array is required. See `help(cslug.ptr) for how "
                "to resolve this.")
        # I'm fairly certain this is impossible.
        raise  # pragma: no cover


def nc_ptr(bytes_like):
    """Retrieve a pointer to a non-contiguous buffer.

    Use with caution. If your function assumes a contiguous array but gets a
    non-contiguous one then you will either get garbage results or memory
    errors.

    """
    return _ptr(bytes_like, 0x18)


_ADDRESS_VIEW = ctypes.ARRAY(ctypes.c_void_p, 100)


def _ptr(bytes_like, flags):
    # https://docs.python.org/3/c-api/buffer.html
    # I'm really not convinced by this.
    obj = ctypes.py_object(bytes_like)
    address = _ADDRESS_VIEW()
    ctypes.pythonapi.PyObject_GetBuffer(obj, address, flags)
    # The above inc-refs it which leads to memory leaks. We should call the
    # following after we're finished with the pointer to safely allow it to be
    # deleted but it's easier just to say always hang onto buffers in Python
    # until you're done with them.
    ctypes.pythonapi.PyBuffer_Release(address)

    # Alternatively, the following is clunkier but safer - maybe switch to this
    # in future, but it makes numpy as dependency.
    # np.frombuffer(bytes_like, dtype=np.uint8).ctypes.data
    return address[0]


if OS == "Windows":  # pragma: no cover
    free_dll_handle = ctypes.windll.kernel32.FreeLibrary
elif OS == "Darwin":  # pragma: no cover
    try:
        lib_system = ctypes.CDLL("libSystem")
    except OSError:
        # Older macOSs. Not only is the name inconsistent but it's
        # not even in PATH.
        _lib_system = "/usr/lib/system/libsystem_c.dylib"
        if os.path.exists(_lib_system):
            lib_system = ctypes.CDLL(_lib_system)
        else:
            lib_system = None
    if lib_system is not None:
        free_dll_handle = lib_system.dlclose
    else:
        # I hope this never happens.
        free_dll_handle = lambda *spam: None
else:  # pragma: no cover
    free_dll_handle = ctypes.CDLL("").dlclose


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
