# -*- coding: utf-8 -*-
"""
Get pointers to buffers using the buffer protocol.

https://docs.python.org/3/c-api/buffer.html

"""

import ctypes


def ptr(bytes_like):
    """Get the raw address of any Python object supporting the C buffer
    protocol.

    A `bytes-like` object is anything for which calling ``memoryview(obj)``
    doesn't raise a :class:`TypeError`. This includes bytes, bytearrays,
    memoryviews, array.arrays and numpy arrays. The output is a subclass of
    :class:`int`.

    .. code-block:: python

        >>> from cslug import ptr
        >>> ptr(bytearray([10, 12, 20, 45]))
        <Void Pointer 140533125025616>

    Pass the output of this function to a C function which expects a pointer.

    On calling this function on a buffer, the buffer's reference count is
    incremented to prevent it from being deleted whilst you're still using it.
    This reference count is decremented on deletion of the pointer returned by
    this function. With this in place, you generally shouldn't need to worry
    about holding onto or releasing memory. There is one exception to this: If
    you use pointer arithmetic, preducts of that arithmitic are just regular
    integers and do not carry the reference.

    If you are using :mod:`numpy` then you should be aware that this method only
    accepts C-contiguous buffers. If you understand how contiguity works and
    have explicitly supported non-contiguous buffers in your C code then you may
    use :meth:`nc_ptr` instead. Otherwise convert your arrays to contiguous ones
    using either::

        array = np.ascontiguousarray(array)

    or::

        array = np.asarray(array, order="C")

    """
    try:
        return PointerType(bytes_like, 0)
    # I'm not sure why the difference but depending on the input, you may get
    # either of these exception types from requesting a contiguous buffer from
    # a non-contiguous one.
    except (ValueError, BufferError) as ex:  # pragma: no branch
        if len(ex.args) == 1 and "not C-contiguous" in ex.args[0]:
            raise ValueError(
                ex.args[0] + " and, by using `ptr()`, you have specified that "
                "a contiguous array is required. See the bottom of "
                "`help(cslug.ptr)` for how to resolve this.") from None
        # I'm fairly certain this is impossible.
        raise  # pragma: no cover


def nc_ptr(bytes_like):
    """Retrieve a pointer to a non-contiguous buffer.

    Use with caution. If your function assumes a contiguous array but gets a
    non-contiguous one then you will either get garbage results or memory
    errors.

    """
    # Yeah, that 0x18 is a hard-coded int flag. It's name is PyBUF_STRIDES.
    return PointerType(bytes_like, 0x18)


# Py_buffer is a structure and its definition, short of copy/pasting from a
# Python.h (which may change), can't be got. Instead just use a void array.
# A Py_buffer is 80 bytes for 64-bit Pythons 3.5 to 3.9 but may grow in later
# versions. Assume a max of 120 bytes to be safe.
Py_buffer = ctypes.ARRAY(ctypes.c_void_p, 120 // ctypes.sizeof(ctypes.c_void_p))


class PointerType(int):
    """A raw pointer which inc-refs the buffer it points to.

    Please no not instantiate this class directly. Instead use the :func:`ptr()`
    function.
    """
    @staticmethod
    def __new__(cls, bytes_like, flags):

        obj = ctypes.py_object(bytes_like)
        # Allocate a Py_buffer.
        _py_buffer = Py_buffer()
        # And populate it.
        ctypes.pythonapi.PyObject_GetBuffer(obj, _py_buffer, flags)
        # The pointer is the 1st item. The rest of the structure is size, shape,
        # strides and writability flags. These can be accessed easier elsewhere.
        address = _py_buffer[0]

        self = super().__new__(cls, address)
        self._py_buffer = _py_buffer
        return self

    def __del__(self):
        # PyObject_GetBuffer() inc-refs the buffer to prevent dangling pointers
        # but leads to memory leaks unless we remember to call the following
        # after we're finished with the pointer to safely allow the buffer to be
        # deleted.
        ctypes.pythonapi.PyBuffer_Release(self._py_buffer)

    def __repr__(self):
        return "<Void Pointer %s>" % super().__repr__()
