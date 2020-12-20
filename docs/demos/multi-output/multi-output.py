import os

os.chdir(os.path.dirname(__file__))

import ctypes
import array
from cslug import CSlug, ptr

slug = CSlug("multi-output.c")

values = array.array("d", range(20))

min_, max_ = ctypes.c_double(), ctypes.c_double()
slug._dll_.range_of(ptr(values), len(values), ctypes.byref(min_),
                    ctypes.byref(max_))

assert min_.value == 0, max_.value == 19


def range_of(values):
    """
    A user friendly wrapper around the raw C ``range_of()`` function.
    """
    # Molly-coddle `values` to make sure it's of the right type.
    if not (isinstance(values, array.ArrayType) and values.typecode == "d"):
        values = array.array("d", values)

    # Create uninitialised `min_` and `max_` values to be written to.
    min_, max_ = ctypes.c_double(), ctypes.c_double()
    # Use `ctypes.byref()` to pass them to C as writable pointers.
    slug._dll_.range_of(ptr(values), len(values), ctypes.byref(min_),
                        ctypes.byref(max_))

    # Return the contents of `min_` and `max_` as native Python floats.
    return min_.value, max_.value


assert range_of([6, 9, 3, 13.5, 8.7, -4]) == (-4., 13.5)
