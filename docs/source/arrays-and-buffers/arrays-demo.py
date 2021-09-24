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
    if not (isinstance(x, array) and x.typecode == int32_t):
        x = array(int32_t, x)

    # Create an array with the same length as `x`.
    # Python really lacks an efficient way to create an empty array,
    out = array(int32_t, [0] * len(x))

    # Call cumsum() C function.
    slug.dll.cumsum(ptr(x), ptr(out), len(x))
    return out


assert cumsum(array(int32_t, [10, 3, 5])) == array(int32_t, [10, 13, 18])

import pytest

pytest.importorskip("numpy")

import numpy as np


def sum_(arr):
    # Ensure `arr` is an array, is of the correct dtype and is C contiguous.
    arr = np.asarray(arr, dtype=np.double, order="C")

    # Find its sum.
    return slug.dll.sum(ptr(arr), len(arr))


assert sum_(np.arange(10)) == 45


def cumsum(x):
    # Normalise `x`.
    x = np.asarray(x, dtype=np.int32, order="C")

    # Create an empty array of the correct size and dtype.
    # Note that ``order="C"`` is already the default - no need to set it.
    out = np.empty(len(x), dtype=np.int32)

    # Call cumsum() C function.
    slug.dll.cumsum(ptr(x), ptr(out), len(x))
    return out


arr = np.arange(10)[::2]
assert np.array_equal(cumsum(arr), arr.cumsum())

# --- Test index raveling formula quoted in docs ---

# 2D

arr = np.arange(6).reshape((2, 3))
shape = arr.shape
i, j = np.broadcast_arrays(np.arange(2)[:, np.newaxis], np.arange(3))
assert i.shape == shape
x = arr

assert np.array_equal(arr, arr.ravel()[i * shape[1] + j])
assert np.array_equal(arr, arr[x // shape[1], x % shape[1]])

# 3D

arr = np.arange(24).reshape((2, 3, 4))
shape = arr.shape
i, j, k = np.broadcast_arrays(
    np.arange(2)[:, np.newaxis, np.newaxis],
    np.arange(3)[:, np.newaxis], np.arange(4))
assert i.shape == shape
x = arr

assert np.array_equal(arr, arr.ravel()[(i * shape[1] + j) * shape[2] + k])
assert np.array_equal(
    arr, arr[x // (shape[1] * shape[2]), (x // shape[2]) % shape[1],
             x % shape[2]])

# --- Vectorization ---


def add_1(arr):
    # Ensure `arr` is an array, is of the correct dtype and is C contiguous.
    arr = np.asarray(arr, dtype=np.intc, order="C")

    # Store the original shape, then flatten `arr` to make it 1D.
    old_shape = arr.shape
    arr = arr.ravel()

    # Set up an empty output array with the same type and shape as `arr`.
    out = np.empty_like(arr)

    # Call the C function on our 1D arrays.
    slug.dll.add_1(ptr(arr), ptr(out), len(arr))

    # Return the output after restoring the original shape.
    return out.reshape(old_shape)


def add_1_(arr):
    # Ensure `arr` is an array, is of the correct dtype and is C contiguous.
    arr = np.asarray(arr, dtype=np.intc, order="C")

    # Create an empty output array with the same type and shape as `arr`.
    out = np.empty_like(arr)

    # Call the C function on our arrays.
    # It doesn't matter that they're not 1D - they look the same to C.
    # Note the length parameter ``arr.size`` instead of ``len(arr)``.
    slug.dll.add_1(ptr(arr), ptr(out), arr.size)

    return out


for add_1 in [add_1, add_1_]:
    assert add_1(10) == 11
    assert np.array_equal(add_1([1, 2, 3]), [2, 3, 4])
    arr = np.arange(24).reshape((2, 3, 4))
    assert np.array_equal(add_1(arr), arr + 1)
    assert np.array_equal(add_1(arr.T), arr.T + 1)
