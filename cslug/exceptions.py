# -*- coding: utf-8 -*-
"""
=======================
:mod:`cslug.exceptions`
=======================

All custom exception and warning classes are defined and accessible here.

"""


class NoGccError(Exception):
    """|gcc| is not in ``PATH`` and the ``CC`` environment variable is unset."""
    def __str__(self):  # pragma: no cover
        """Provide some explanation on how to install gcc.

        Contributions welcome here.
        """
        import shutil
        import platform
        import sys

        # ---
        # If all we need is one line of code to a package manager then give the
        # user that line.
        if platform.system() == "Darwin":
            # macOS.
            cmd = "sudo port install mingw-w64"

        elif platform.system() == "FreeBSD":
            # FreeBSD.
            cmd = "pkg install gcc"

        elif shutil.which("pacman"):
            # Some Linux distros (Manjaro) and msys2.
            cmd = "pacman -S gcc"
            if sys.platform != "msys":  # pragma: no cover
                # msys2 doesn't have sudo.
                cmd = "sudo " + cmd

        elif shutil.which("apt"):
            # Ubuntu Linux.
            cmd = "sudo apt install gcc"

        else:
            # Windows, most Linux distributions and unknown OSs.
            cmd = None

        out_ = "Building requires gcc to be installed and in your PATH. {}" \
               "Alternatively, set the CC environment variable to the " \
               "name of any supported compiler in PATH, or the full path of " \
               "a compiler which need not be in PATH."

        if cmd:
            return out_.format(f"Get it by running:\n    {cmd}\n"
                               f"in bash/terminal. ")

        # Installing on Windows is a bit strange. The easiest method seems to be
        # Mingw-builds.
        if platform.system() == "Windows":
            return out_.format(
                "Download Mingw-builds from:\n"
                "    http://mingw-w64.org/doku.php/download/mingw-builds\n"
                "Install it, making sure to select:\n    Architecture: "
                f"{'i686' if sys.maxsize == (1 << 31) - 1 else 'x86_64'}\n"
                "Then add its 'bin' folder "
                r"(e.g C:\Program Files\mingw-w64\mingw64\bin) "
                "to the 'PATH' environment variable. ")

        return out_.format("")


class CCNotFoundError(Exception):
    """The ``CC`` environment variable is set but could not be found."""
    def __str__(self):
        from os.path import dirname
        path, = self.args
        if dirname(path):
            return "The CC variable specifies the compiler {} which does not " \
                   "exist.".format(path)
        return "The CC variable specifies the compiler {} which could not be " \
               "found in PATH. Try adding your compiler's location to PATH or" \
               " setting CC to a full path to your compiler.".format(path)


class BuildError(Exception):
    """Compiler raised an error during a compile."""
    def __str__(self):
        return "The build command:\n\n%s\n\nFailed with:\n\n%s\n" % self.args


class BuildBlockedError(Exception):
    """The ``CC`` environment variable is set to ``!block``. (For testing.)"""
    def __str__(self):
        return "The build was blocked by the environment variable `CC=!block`."


class LibraryOpenElsewhereError(BuildError):
    """Writing to a DLL raised a misleading permission error."""
    def __str__(self):
        path, = self.args
        return f"Writing to {path} failed because it is open in another " \
               f"program. cslug closed any open handles in this instance of " \
               f"Python. Are you running cslug in another Python console?"


class BuildWarning(Warning):
    """Compiler issued a build warning."""
    pass


class PrintfWarning(Warning):
    """C source code contains I/O functions which write to true stdout. These
    are not generally redirectable and will therefore be invisible if run from
    an IDE rather than a terminal."""
    pass


class TypeParseWarning(Warning):
    """An argument or return type was not recognised."""
    pass
