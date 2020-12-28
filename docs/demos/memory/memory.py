import os

os.chdir(os.path.dirname(__file__))

import ctypes
from cslug import CSlug, stdlib

slug = CSlug("memory.c")
slug.make()

class FreeWith(object):
    def __init__(self, handle, obj):
        self.handle = handle
        if hasattr(obj, "_memory_handles"):
            obj._memory_handles.append(self)
        else:
            obj._memory_handles = [self]

    def __del__(self):
        stdlib.free(self.handle)


def free_with(handle, obj):
    FreeWith(handle, obj)
    return obj


def indices_of(x, y):
    count = ctypes.c_int()
    out_ptr = slug.dll.indices_of(x, len(x), y, ctypes.byref(count))
    return free_with(out_ptr,
                     (ctypes.c_int * count.value).from_address(out_ptr))


indices_of(b"cabbages", b"a")

def indices_of_(x, y):
    count = ctypes.c_int()
    out_ptr = slug.dll.indices_of_no_precount(x, len(x), y, ctypes.byref(count))
    return free_with(out_ptr,
                     (ctypes.c_int * count.value).from_address(out_ptr))
