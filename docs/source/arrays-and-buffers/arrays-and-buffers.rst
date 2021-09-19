==================
Buffers and Arrays
==================

There exists a lesser known family of objects within the more C-ish corners of
Python known as the *bytes-like* objects.
These are objects which, using the `Buffer Protocol`_, agree to have their raw
contents read from and written to by other (usually C) code.
Or in more C like terms, these objects give you a void |../pointer| to their
data and you're free to do what you like with it.

This family includes the standard types:

- :class:`bytes`
- :class:`bytearray`
- :class:`memoryview`
- :class:`array.array`

As well as a few 3\ :superscript:`rd` party objects:

- :class:`numpy.ndarray`

To get a pointer to a bytes-like object, pass it to :func:`cslug.ptr()`. ::

    >>> from cslug import ptr
    >>> ptr(b"bytes")
    <Void Pointer 139814594392528>
    >>> ptr(bytearray([1, 2, 3]))
    <Void Pointer 139814617576144>
    >>> import array
    >>> ptr(array.array("i", [4, 5, 6]))
    <Void Pointer 139814617576112>

Those long numbers inside the :class:`cslug.PointerType` reprs are the memory
addresses of the buffers/arrays we provided. :class:`~cslug.PointerType` is a
subclass of :class:`int` and can therefore be passed directly to any C function
which expects a pointer.

This is arguably the lowest level of |cslug|\ 's Python/C bridging meaning that
it is simultaneously the fastest (absolutely no unnecessary copying) but also
the easiest way to crash Python. You have been warned...


Buffers
-------

Bytes (both :class:`bytes` its writable cousin, the :class:`bytearray`) are the
simplest to work with:

* Declare a C function taking a :c:`char *` or :c:`void *` to an array of bytes
  and an integer specifying the length of the given array.

    .. code-block:: C

        void do_something(void * x, int len_x) {
          // Put something interesting in here. Most likely some for loop...
          for (int i = 0; i < len_x; i++) {
            // ... which reads or writes to `x[i]`.
            x[i];
          }
        }

* Pass :func:`ptr(buffer) <cslug.ptr>` to it in Python.

    .. code-block:: python

        x = bytearray([67, 98, 32])
        slug.dll.do_something(ptr(x), len(x))

If your function modifies the buffer, make sure you use mutable
:class:`bytearray` instead of read-only :class:`bytes`.

If you want to create a new buffer from scratch in C and pass it to Python then
you're in for a bit of a disappointment because,
as it was when :ref:`writing strings <Writing to strings>`, returning a block of
memory is disproportionally dangerous in C.
Instead, create an empty writeable buffer in Python
(:py:`out = bytearray(length)`), then pass that buffer to C to populate it.

--------------------------------------------------------------------------------

Arrays
------

Arrays from the :mod:`array` standard library module are almost the same as
buffers but with one more thing to watch out for:

* The *typecode* of the array passed to a C function must match the type of
  pointer specified as the argtype of that function.

So for the following C function:

.. literalinclude:: arrays-demo.c
    :language: C
    :caption: totals.c
    :name: totals.c
    :end-at: }

Loaded into Python with:

.. literalinclude::  arrays-demo.py
    :language: python
    :start-at: import array
    :end-at: slug =

The :c:`double sum(double * arr, int len_arr)` function expects a to receive a
:c:`double *` (AKA an array of doubles) so we must give it one.
Types in :mod:`array` are specified with *typecodes*.
Looking at `array's table of type codes`_, :py:`'d'` is the type code for
doubles.

    >>> arr = array.array("d", [10, 11, 12])
    >>> slug.dll.sum(ptr(arr), len(arr))
    33.0

The safety nets of :mod:`ctypes` and |cslug| both fall short on array item
types.
There is no type checking. If you get it wrong, you just get bogus results,

    >>> arr = array.array("f", [10, 11, 12])
    >>> slug.dll.sum(ptr(arr), len(arr))
    1048576.2543945312  # 10 + 11 + 12 is not this!

It's therefore best to put your own check/conversion in.

.. literalinclude:: arrays-demo.py
    :start-at: def sum_
    :end-at: return

Now you can give it more or less anything (although it'll be much faster if you
give it the correct type)::

    >>> sum_(range(10))
    45.0


Benchmarks
..........

With the correct types this C version of ``sum()`` is 16 times faster than the
builtin :func:`sum`.

    >>> from sloth.simple import time_callable  # Use `pip install sloth-speedtest`.
    >>> arr = array.array("d", range(100000))
    >>> time_callable(sum, 100, arr) / time_callable(sum_, 100, arr)
    16.31841284669072

But with the wrong types it's 4-5 times slower.

    >>> arr = range(100000)
    >>> time_callable(sum, 100, arr) / time_callable(sum_, 100, arr)
    0.22091244446076183

In short, to get the most out of C, you need to pick a type and stick to it. If
you want to duck-type, use Python.


Exact types
...........

You may also notice that `array's table of type codes`_ lacks the exact types
from :c:`#include <stdint.h>`.
Use the :func:`cslug.misc.array_typecode()` helper function to get them.
e.g. If your C function has an argument of type :c:`uint16_t *` then use::

    >>> from cslug.misc import array_typecode
    >>> arr = array.array(array_typecode("uint16_t"), arr)
    >>> arr
    array('H', [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    >>> arr.itemsize
    2


Writing an array
................

Write an array by populating an empty one.
For example this uninspiring C function takes an input array which it reads from
and an output array where it writes what you'd typically return in Python.

.. literalinclude:: arrays-demo.c
    :language: C
    :name: cumsum
    :start-at: #include
    :end-before: // ---

The above may be wrapped with something like the following.

.. literalinclude:: arrays-demo.py
    :start-at: from cslug.misc import array_typecode
    :end-at: return


.. _`Buffer Protocol`: https://docs.python.org/3/c-api/buffer.html
.. _`array's table of type codes`: https://docs.python.org/3.8/library/array.html#module-array
