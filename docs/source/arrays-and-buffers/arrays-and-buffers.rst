================================
Buffers, Arrays and NumPy Arrays
================================

There exists a lesser known family of objects within the more C-ish corners of
Python known as the *bytes-like* objects.
These are objects which, using the `Buffer Protocol`_, agree to have their raw
contents read from and written to by other (usually C) code.
Or in more C like terms, these objects give you a void |pointer| to their data
and you're free to do what you like with it.

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

* Declare your C function arguments as :c:`char *` or :c:`void *`.

    .. code-block:: C

        void do_something(void * x, int len_x) {
          for (int i = 0; i < len_x; i++) {
            // Put something interesting in here.
            x[i];
          }
        }

* Pass :py:`ptr(buffer)` to it in Python.

    .. code-block:: python

        slug.dll.do_something(ptr(bytearray([67, 98, 32])))

If your function modifies the buffer, make sure you use mutable
:class:`bytearray` instead of read-only :class:`bytes`.

If you want to create a new buffer from scratch in C and pass it to Python then
don't.
As it was when :ref:`writing strings <Writing to strings>`, returning a block of
memory is disproportionally fiddly and dangerous.
Instead, create an empty writeable buffer in Python
(:py:`out = bytearray(length)`), then pass that buffer to C to populate it.
