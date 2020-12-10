# -*- coding: utf-8 -*-
"""
"""

import ctypes


def ptr(bytes_like):
    """Get the raw address of any Python object supporting the C buffer
    protocol.

    A `bytes-like` object is anything for which calling ``memoryview(obj)``
    doesn't raise a :class:`TypeError`. This includes bytes, bytearrays,
    memoryviews, array.arrays and numpy arrays.

    This intentionally doesn't inc-ref the buffer so don't let it be deleted in
    Python until C is done with it. i.e. ``c_method(ptr(b"buffer"))`` will
    likely crash Python. Instead use:

    .. code-block:: python

        buffer = b"buffer"
        c_method(ptr(buffer))

        # Now it is safe to delete the buffer (or leave Python's gc to do it
        # automatically as you normally would any other Python object).
        del buffer # optional

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
        return _ptr(bytes_like, 0)
    # I'm not sure why the difference but depending on the input, you may get
    # either of these exception types from requesting a contiguous buffer from
    # a non-contiguous one.
    except (ValueError, BufferError) as ex:  # pragma: no branch
        if len(ex.args) == 1 and "not C-contiguous" in ex.args[0]:
            raise ValueError(
                ex.args[0] + " and, by using `ptr()`, you have specified that "
                "a contiguous array is required. See `help(cslug.ptr) for how "
                "to resolve this.")
        # I'm fairly certain this is impossible.
        raise  # pragma: no cover


def nc_ptr(bytes_like):
    """Retrieve a pointer to a non-contiguous buffer.

    Use with caution. If your function assumes a contiguous array but gets a
    non-contiguous one then you will either get garbage results or memory
    errors.

    """
    return _ptr(bytes_like, 0x18)


_ADDRESS_VIEW = ctypes.ARRAY(ctypes.c_void_p, 100)


def _ptr(bytes_like, flags):
    # https://docs.python.org/3/c-api/buffer.html
    # I'm really not convinced by this.
    obj = ctypes.py_object(bytes_like)
    address = _ADDRESS_VIEW()
    ctypes.pythonapi.PyObject_GetBuffer(obj, address, flags)
    # The above inc-refs it which leads to memory leaks. We should call the
    # following after we're finished with the pointer to safely allow it to be
    # deleted but it's easier just to say always hang onto buffers in Python
    # until you're done with them.
    ctypes.pythonapi.PyBuffer_Release(address)

    # Alternatively, the following is clunkier but safer - maybe switch to this
    # in future, but it makes numpy as dependency.
    # np.frombuffer(bytes_like, dtype=np.uint8).ctypes.data
    return address[0]
