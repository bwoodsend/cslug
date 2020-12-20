# -*- coding: utf-8 -*-
"""
"""

import io
import warnings
import ctypes

from cslug import CSlug, anchor

import pytest

from tests import name

pytestmark = pytest.mark.order(-2)


def test_struct_io():

    slug = CSlug(
        anchor(name()),
        io.StringIO("""

    typedef struct Thing{
        int a;
        float b;
    } Thing;

    int get_a(Thing * thing) {
        return thing -> a;
    }

    float get_b(Thing * thing) {
        return thing -> b;
    }

    void set_a(Thing * thing, int a) {
        thing -> a = a;
    }

    void set_b(Thing * thing, float b) {
        thing -> b = b;
    }

    Thing make_thing(int a, float b) {
        Thing thing;
        thing.a = a;
        thing.b = b;
        return thing;
    }

    int get_a_plus_x(Thing thing, int x) {
        return thing.a + x;
    }

    """))

    with warnings.catch_warnings():
        warnings.filterwarnings("error")
        lib = slug._dll_

    assert hasattr(lib, "Thing")

    assert lib.get_a.argtypes == [ctypes.c_void_p]

    assert lib.make_thing.argtypes == [ctypes.c_int, ctypes.c_float]
    assert lib.make_thing.restype == lib.Thing
    assert lib.get_a_plus_x.argtypes == [lib.Thing, ctypes.c_int]
    assert lib.get_a_plus_x.restype == ctypes.c_int

    thing = lib.Thing(10, 3)
    assert lib.get_a(thing._ptr) == thing.a == 10
    assert lib.get_b(thing._ptr) == thing.b == 3.0
    assert repr(thing) == "Thing(a=10, b=3.0)"

    lib.set_a(thing._ptr, 5)
    lib.set_b(thing._ptr, 12)
    assert lib.get_a(thing._ptr) == thing.a == 5
    assert lib.get_b(thing._ptr) == thing.b == 12.0


def test_long_repr():
    slug = CSlug(
        anchor(name()),
        io.StringIO("""

    #include <stdint.h>

    typedef struct LongNamedThing{
        int64_t very_long_name_1; int64_t very_long_name_2;
        int64_t very_long_name_3; int64_t very_long_name_4;
    } LongNamedThing;

    """))

    thing = slug._dll_.LongNamedThing(*(range(4)))

    assert repr(thing) == """
LongNamedThing(very_long_name_1=0, very_long_name_2=1,
               very_long_name_3=2, very_long_name_4=3)
""".lstrip()

    thing = slug._dll_.LongNamedThing(*(1 << 30 << i for i in range(4)))

    assert repr(thing) == """
LongNamedThing(very_long_name_1=1073741824,
               very_long_name_2=2147483648,
               very_long_name_3=4294967296,
               very_long_name_4=8589934592)
""".lstrip()


def test_empty():
    slug = CSlug(anchor(name()), io.StringIO("typedef struct Empty {} Empty;"))

    thing = slug._dll_.Empty()

    assert repr(thing) == "Empty()"
