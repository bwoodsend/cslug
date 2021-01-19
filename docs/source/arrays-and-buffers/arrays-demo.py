from array import array
from cslug import CSlug, ptr, anchor

slug = CSlug(anchor("arrays-demo.c"))

slug.make()
assert slug.dll.sum(ptr(array("d", [10, 11, 12])), 3) == 33.0


def sum_(arr):
    """Wrapper for the ``sum()`` function from ``arrays-demos.c``."""
    # If not the correct type:
    if not (isinstance(arr, array) and arr.typecode == "d"):
        # Make it the correct type.
        arr = array("d", arr)
    # Run the C function.
    return slug.dll.sum(ptr(arr), len(arr))


assert sum_(range(10)) == 45

from cslug.misc import array_typecode

int32_t = array_typecode("int32_t")


def cumsum(x):
    # Some form of type check.
    if not (isinstance(int32_t, array) and x.typecode == int32_t):
        x = array(int32_t, x)

    # Create an array with the same length as `x`.
    # Python really lacks an efficient way to create an empty array,
    out = array(int32_t, [0] * len(x))

    # Call cumsum() C function.
    slug.dll.cumsum(ptr(x), ptr(out), len(x))
    return out


assert cumsum(array(int32_t, [10, 3, 5])) == array(int32_t, [10, 13, 18])
