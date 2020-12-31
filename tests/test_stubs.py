# -*- coding: utf-8 -*-
"""
"""

import io

import pytest

from cslug import Types


def test_empty():
    self = Types(io.StringIO(), io.StringIO())
    self.init_from_source()
    assert self.pyi_stubs() == """\
import ctypes
from cslug import CSlug
class slug(CSlug):
    class dll(ctypes.CDLL):
        pass
"""
    exec(self.pyi_stubs(), locals(), locals())

    self.pyi_namespace = ""
    assert self.pyi_stubs() == """\
import ctypes
from cslug import CSlug
"""
    exec(self.pyi_stubs(), locals(), locals())


def test_functions():
    self = Types(io.StringIO(), io.StringIO("""\
int f(float x) {}
float g(double y) {}
char ignore_me();
"""))

    self.init_from_source()
    assert self.pyi_stubs() == """\
import ctypes
from cslug import CSlug
class slug(CSlug):
    class dll(ctypes.CDLL):
        f = ctypes.CFUNCTYPE(ctypes.c_int)()
        g = ctypes.CFUNCTYPE(ctypes.c_float)()
"""
    exec(self.pyi_stubs(), locals(), locals())

    self.pyi_namespace = ""
    assert self.pyi_stubs() == """\
import ctypes
from cslug import CSlug
f = ctypes.CFUNCTYPE(ctypes.c_int)()
g = ctypes.CFUNCTYPE(ctypes.c_float)()
"""
    exec(self.pyi_stubs(), locals(), locals())

    self.headers.append(io.StringIO("char prototype();"))
    self.init_from_source()
    assert self.pyi_stubs() == """\
import ctypes
from cslug import CSlug
f = ctypes.CFUNCTYPE(ctypes.c_int)()
g = ctypes.CFUNCTYPE(ctypes.c_float)()
prototype = ctypes.CFUNCTYPE(ctypes.c_char)()
"""
    exec(self.pyi_stubs(), locals(), locals())

