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

from cslug import misc, exceptions, c_parse, Types
from cslug._headers import Header
from cslug._cc import cc, cc_version, mmacosx_version_min, macos_architecture
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
DEFAULT_LINKS = ["m"] if OS == "Linux" else []
EXPORT_SYMBOLS = {
    "tcc": "-rdynamic",
    "pcc": "-rdynamic",
    "gcc": "-fPIC",
    "clang": "" if OS == "Windows" else "-fPIC",
}


class CSlug(object):
    """Compiles and loads C code in a relatively safe and streamlined manner.
    """
    def __init__(self, path, *sources, headers=(), links=(), flags=()):
        """

        Args:
            path (str or os.PathLike or list):
            *sources (str or os.PathLike or io.TextIOBase):
                C source code files. May also be lists of files.
            headers (cslug.Header or list[cslug.Header]):
                cslug generated headers - not just ``*.h`` files (which |cslug|
                doesn't need to see anywhere).
            links (str or list[str]):
                Other C libraries to link to via the ``-l`` compiler switch.
                Should not contain the ``-l`` prefix or platform suffix.
            flags (str or list[str]):
                Additional flags to be passed directly to the C compiler.
                Can also be configured using the ``CC_FLAGS`` environment
                variable. Inspect using :meth:`compile_command`.

        .. versionchanged:: 0.3.0

            Add **flags** parameter and the ``CC_FLAGS`` variable.

        """
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
        self.links = misc.flatten(links)
        for link in DEFAULT_LINKS:  # pragma: Linux
            if link not in self.links:
                self.links.append(link)
        for h in self.headers:
            if not isinstance(h, Header):
                raise TypeError(
                    "The `headers` argument must be of `cslug.Header()` type, "
                    "not {}.".format(type(h)))
        self.types_map = Types(path.with_suffix(".json"), *self.sources)
        self._dll = None
        self.flags = [str(i) for i in misc.flatten(flags)]

    def compile(self):
        """Recompile C code only.

        Returns:
            bool:
                True if the compile succeeded. However this is redundant because
                an error is raised if it didn't.

        Raises:
             exceptions.BuildError:
                Any compiler errors are propagated as Python exceptions.

        Warns:
            exceptions.BuildWarning:
                Any build warnings from the compiler are propagated as Python
                warnings.

        """
        self.close()

        # This would be a simple subprocess.run() if it weren't for having
        # multiple stdins to pipe in. That being said, I'm pretty certain that
        # this doesn't work anyway (see comments below).
        command, buffers = self.compile_command()

        # gcc 10.2 (the only compiler to support both Windows and unicode)
        # expects utf-8 input - irregardless of codepage.
        p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                  encoding="utf-8")

        # Write pseudo files to stdin. I strongly suspect that this is simply
        # concatenating them into one input rather than writing separate files.
        for buffer in buffers:
            p.stdin.write(misc.read(buffer)[0])

        # Close everything, wait for completion then check for error messages.
        p.stdin.close()
        p.wait()
        msg = p.stderr.read()
        p.stderr.close(), p.stdout.close()

        # If error message is just whitespace:
        if not re.search(r"\S", msg):
            # Make it empty.
            msg = ""

        # If build failed:
        if p.returncode:
            # If the DLL is open, you get a permission error on Windows.
            # This misleads you into thinking you should run as admin which
            # won't help at all.
            # Catch and reraise with something less cryptic.
            if re.search("(?:open output|write).*permission denied", msg,
                         re.DOTALL | re.IGNORECASE):  # pragma: no cover
                raise exceptions.LibraryOpenElsewhereError(self.path)
            raise exceptions.BuildError(command, msg)

        if msg:
            # Propagate any compiler warnings.
            warnings.warn(msg, category=exceptions.BuildWarning)
        return True

    def close(self, all=True):
        """Close the library stored in :attr:`CSlug.dll`.

        Args:
            all(bool):
                Close any other existing handles to the same file.

        Closing is required before a recompile to avoid permission errors or
        dangling pointers.
        If the library is already closed, this function silently does nothing.

        """
        if all:
            new = []
            for slug in _slug_refs[self.path]:
                # Close any other CSlugs that use the same DLL. This prevents a
                # PermissionErrors or seg-faults if the user create a
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
        """The open C library.

        Returns:
            ctypes.CDLL:

        This attribute is lazily loaded. On first access, this :class:`property`
        will:

        * Check the library has been compiled and invoke a full compile with
          :meth:`make` if it hasn't.
        * Open the library.
        * Initialise type information for all known symbols (functions).

        Use :meth:`close` to reset.

        """
        # If not already loaded:
        if self._dll is None:

            # Get name to be passed to ctypes.CDLL().
            path = str(self.path)
            if not self.path.is_absolute():
                # Relative paths must be prefixed with ./ to prevent them being
                # searched for in PATH.
                path = os.path.join(".", str(path))

            # If anything is missing:
            if not (self.path.exists() and self.types_map.json_path.exists()):
                # Recompile everything.
                self.make()

            # Load the DLL.
            dll = ctypes.CDLL(path)
            # Load the types.
            self.types_map.init_from_json()
            # Set the types from self.types_map to the dll.
            self.types_map.apply(dll)
            # Cache the dll.
            self._dll = dll

        return self._dll

    def make(self):
        """Invoke a full recompile and refresh of *everything*.

        Returns:
            bool: True if the build succeeded.

        *Everything* here is defined as the following sequence in the
        following order:

        1. :meth:`close` any open handles.
        2. Rebuild each :class:`Header` in :attr:`!headers` using
           :meth:`Header.make`.
        3. Recompile the shared library using :meth`compile`.
        4. Rescan C source code for type information and write it to a json
           file.

        The C library is loaded back into Python on next access of :attr:`dll`.

        """
        self.close()
        for header in self.headers:
            header.make()
        ok = self.compile()
        self.types_map.make()
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
        """Get the compile command invoked by :meth:`compile`.

        I hope to eventually make this function configurable.
        """
        _cc = cc(_cc)
        cc_name, version = cc_version(_cc)

        # Output filename
        output = ["-o", str(self.path)]

        # Create a library, exporting all symbols.
        flags = ["-shared"]
        if EXPORT_SYMBOLS[cc_name]:  # pragma: no cover
            flags.append(EXPORT_SYMBOLS[cc_name])

        if cc_name == "gcc" and version >= (4, 6, 0) \
            or cc_name == "clang" and version >= (3, 7, 0):  # pragma: no cover
            # Optimize for speed.
            flags.append("-O3")

        # Compile for older versions of macOS.
        if cc_name in ("gcc", "clang") and OS == "Darwin":  # pragma: no cover
            flags += [f"-mmacosx-version-min={mmacosx_version_min()}"]

        if cc_name == "gcc":  # pragma: no cover
            # I've only seen this needed on manylinux docker images.
            flags.append("--std=c99")

        # Set 32 bit only if needed. Forcing `-m64` causes aarch64 to fail
        # because it interprets it as x86_64.
        # XXX: This will still break 32bit platforms other than i386 such as
        #      aarch32.
        if BIT_NESS != 64:  # pragma: no cover
            flags += ["-m" + str(BIT_NESS)]

        # If on macOS, we may be cross compiling for Apple's new ARM chip.
        if OS == "Darwin":  # pragma: no cover
            # If the user has explicitly requested a cross compile via the
            # MACOS_ARCHITECTURE environment variable then set the -arch
            # flag to match.
            arch = macos_architecture()
            if arch == "universal2":
                flags.extend(["-arch", "x86_64", "-arch", "arm64"])
            elif arch:
                flags.extend(["-arch", arch])

        # Super noisy build warnings.
        warning_flags = "-Wall -Wextra".split()

        # Custom flags from the CC_FLAGS environment variable. Delimited
        # with whitespace.
        env_flags = re.findall(r"[^\s]+", os.environ.get("CC_FLAGS", ""))

        # Compile all .c files into 1 combined library.
        # Note that you don't pass header files to compilers.
        true_files = [str(i) for i in self.sources if isinstance(i, Path)
                      if i.suffix != ".h"]  # yapf: disable
        buffers = [i for i in self.sources if not isinstance(i, Path)]

        stdin_flags = "-x c -".split() if buffers else []

        link_flags = ["-l" + i for i in self.links]

        return ([_cc] + output + flags + warning_flags + self.flags +
                env_flags + true_files + stdin_flags + link_flags, buffers)

    def _check_printfs(self):
        return any(check_printfs(*misc.read(i)) for i in self.sources)


# Create a global register of CSlugs grouped by DLL filename. This will be used
# by CSlug.close(all=True)
try:
    _slug_refs
except NameError:
    _slug_refs = collections.defaultdict(list)


def check_printfs(text, name=None):
    """Test and warn for :c:`printf()`\\ s in C code.

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
