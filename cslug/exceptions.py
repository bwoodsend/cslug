# -*- coding: utf-8 -*-
"""
"""


class NoGccError(Exception):
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
            cmd = "su pkg install gcc"

        elif shutil.which("pacman"):
            # Some Linux distros (Manjaro) and msys2.
            cmd = "pacman -S gcc"
            if sys.platform != "msys":  # pragma: no cover
                # msys2 doesn't have sudo.
                cmd = "sudo " + cmd

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
    def __str__(self):
        return "The build command:\n\n%s\n\nFailed with:\n\n%s\n" % self.args


class BuildBlockedError(Exception):
    def __str__(self):
        return "The build was blocked by the environment variable `CC=!block`."


class LibraryOpenElsewhereError(BuildError):
    def __str__(self):
        path, = self.args
        return f"Writing to {path} failed because it is open in another " \
               f"program. cslug closed any open handles in this instance of " \
               f"Python. Are you running cslug in another Python console?"


class BuildWarning(Warning):
    pass


class PrintfWarning(Warning):
    pass


class TypeParseWarning(Warning):
    pass
