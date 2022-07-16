# -*- coding: utf-8 -*-
"""
Get pointers to buffers using the buffer protocol.

https://docs.python.org/3/c-api/buffer.html

"""

from cslug.__pointers import Pointer as PointerType, PyBUF_STRIDES


def ptr(bytes_like):
    """Get the raw address of any Python object supporting the C buffer
    protocol.

    A *bytes-like* object is anything for which calling ``memoryview(obj)``
    doesn't raise a `TypeError`. This includes `bytes`, `bytearray`,
    `memoryview`, `array.array` and `numpy.array`. The output is a subclass of
    `int`.

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
    you use pointer arithmetic, preducts of that arithmetic are just regular
    integers and do not carry the reference.

    If you are using `numpy` then you should be aware that this method only
    accepts C-contiguous buffers. If you understand how contiguity works and
    have explicitly supported non-contiguous buffers in your C code then you
    may use `nc_ptr` instead. Otherwise convert your arrays to contiguous ones
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
    return PointerType(bytes_like, PyBUF_STRIDES)
