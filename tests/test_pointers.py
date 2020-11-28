# -*- coding: utf-8 -*-
"""
"""

import os
import sys
import array

import pytest

from cslug import ptr, nc_ptr


@pytest.mark.parametrize("ptr", [ptr, nc_ptr])
def test_ptr(ptr):
    a = array.array("i", range(100))
    assert a.buffer_info() == (ptr(a), len(a))
    assert a.buffer_info() == (ptr(memoryview(a)), len(a))

    if sys.version_info >= (3, 8):
        assert a.buffer_info() == (ptr(memoryview(a).toreadonly()), len(a))

    # bytes() and bytearray() make copies so the ids won't match. Still check
    # we can get their pointers though.
    ptr(bytes(a))
    ptr(bytearray(a))

    with pytest.raises(TypeError):
        ptr("not bytes-like")
    with pytest.raises(TypeError):
        ptr(12)


def test_strided():
    # Create a multidimensional PyBuffer using memoryview(). In practice, users
    # will more likely use multi-dimensional numpy array.
    _a = array.array("i", range(100))
    a = memoryview(_a).cast("b", (10, 10, _a.itemsize))
    address = _a.buffer_info()[0]

    assert ptr(a) == address
    assert nc_ptr(a) == address

    with pytest.raises(ValueError):
        ptr(a[::2])

    # I would put more tests here but memoryview doesn't support them.

    assert nc_ptr(a[::2]) == address


# Gobble up memory in 256MB chunks.
MEM_BLOCK_SIZE = 1 << 28

# Maximum amount of memory-use increase. Should be almost zero if not zero.
# Certainly much less than MEM_BLOCK_SIZE.
MEM_LEAK_TOL = MEM_BLOCK_SIZE // 100


def leaks(f, tol=None, n=1):
    """
    Test if a function leaks memory.

    Tracks the memory usage of this process (i.e Python) before and after
    calling ``f()`` ``n`` times and returns the difference in bytes. If **f**
    cleans itself up correctly the output should be roughly zero.
    """
    # psutil isn't supported on msys2, hence the not making it a strict test
    # dependency.
    pytest.importorskip("psutil")
    import psutil

    p = psutil.Process(os.getpid())
    old = p.memory_info().vms
    for i in range(n):
        f()
    new = p.memory_info().vms
    out = new - old
    if tol is not None:
        assert out <= tol
    return out


def test_leaks():
    """Sanity check that :meth:`leaks` works."""
    a = []
    with pytest.raises(AssertionError):
        leaks(lambda: a.append(bytes(MEM_BLOCK_SIZE)), MEM_LEAK_TOL)


def test_ptr_leaks():
    leaks(lambda: ptr(bytes(MEM_BLOCK_SIZE)), MEM_LEAK_TOL)
    leaks(lambda: nc_ptr(bytes(MEM_BLOCK_SIZE)), MEM_LEAK_TOL)
