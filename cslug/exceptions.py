# -*- coding: utf-8 -*-
"""
"""


class NoGccError(Exception):

    def __str__(self):
        return "Building requires gcc to be installed and in your PATH."


class BuildError(Exception):

    def __str__(self):
        return "The build command:\n\n%s\n\nFailed with:\n\n%s\n" % self.args


class BuildWarning(Warning):
    pass


class TypeParseWarning(Warning):
    pass
