import os

os.chdir(os.path.dirname(__file__))

import ctypes
from cslug import CSlug

slug = CSlug("reverse.c")
slug.make()

in_ = "Reverse this string."

out = ctypes.create_unicode_buffer(len(in_))
slug.dll.reverse(in_, out, len(in_))

assert out.value == in_[::-1]


def reverse(in_):
    """
    Returns a :class:`str` in reverse order.
    """
    out = ctypes.create_unicode_buffer(len(in_))
    slug.dll.reverse(in_, out, len(in_))
    return out.value


assert reverse(in_) == in_[::-1]
