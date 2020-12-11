# -*- coding: utf-8 -*-
"""
"""


class NoGccError(Exception):
    def __str__(self):
        return "Building requires gcc to be installed and in your PATH. " \
               "Alternatively, set the CC environment variable to the " \
               "filename of any supported compiler."


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
        return "The build was blocked by the environment variable `CC=block`."


class BuildWarning(Warning):
    pass


class PrintfWarning(Warning):
    pass


class TypeParseWarning(Warning):
    pass
