# -*- coding: utf-8 -*-
"""
"""

from cslug import CSlug, anchor, ptr, nc_ptr

slug = CSlug(anchor("flatten.c"))
slug.make()

import pytest

pytest.importorskip("numpy")
import numpy as np


def flatten_3D(arr):
    """Wrapper for ``flatten_3D()``."""

    # Normalise `arr`.
    arr = np.asarray(arr, dtype=np.double, order="C")
    # Sanity check that `arr` is 3D.
    assert arr.ndim == 3

    # Create a flat empty output array to populate.
    out = np.empty(arr.size, arr.dtype)

    # Pass `arr`, `out` and the shape of `arr` to the C function.
    # Note the use of `arr.ctypes.shape` which is a ctypes size_t array,
    # instead of `arr.shape` which is a tuple.
    slug.dll.flatten_3D(ptr(arr), ptr(out), ptr(arr.ctypes.shape))

    return out


def flatten_strided_3D(arr):
    """Wrapper for ``flatten_strided_3D()``."""

    # Normalise array dtype but no need to enforce contiguity.
    arr = np.asarray(arr, dtype=np.double)
    assert arr.ndim == 3

    # As before, create a flat empty output array to populate.
    out = np.empty(arr.size, arr.dtype)

    # Pass the arrays, the shape and strides to C.
    # Note, you must use `nc_ptr(arr)` instead of `ptr()` because `arr` is
    # not necessarily contiguous.
    slug.dll.flatten_strided_3D(nc_ptr(arr), ptr(out), ptr(arr.ctypes.shape),
                                ptr(arr.ctypes.strides))
    return out


arr: np.ndarray = np.arange(24, dtype=np.double).reshape((2, 3, 4))
assert np.array_equal(arr.ravel(), flatten_3D(arr))
assert np.array_equal(arr.T.ravel(), flatten_3D(arr.T))
assert np.array_equal(arr.ravel(), flatten_strided_3D(arr))
assert np.array_equal(arr.T.ravel(), flatten_strided_3D(arr.T))
