Return multiple values from a function
--------------------------------------

In Python, if a function has more than one output you return a tuple. In C, the
best you can do is :ref:`return a struct <Passing a Struct from C to Python>`
which is a lot of work for something so simple. Alternatively you can pass
arguments by reference which the C function can write to.

**For example**, the following function has two outputs, even though it doesn't
use a return value. Instead it takes pointer inputs ``min`` and ``max`` which
will be written to:

.. literalinclude:: ../../demos/multi-output/multi-output.c
    :language: C
    :caption: multi-output.c

To use it we the usual setup:

.. literalinclude:: ../../demos/multi-output/multi-output.py
    :start-at: import ctypes
    :end-at: slug =

We do have to do some leg-work to interact with this function. Lets give ourselves
an input array of the correct type we'd like to use::

    values = array.array("d", range(20))

Now to finally run our C code. The :func:`ctype.byref` calls are where the magic
is happening.

.. literalinclude:: ../../demos/multi-output/multi-output.py
    :start-at: # Create uninitialised
    :end-at: ctypes.byref(max_))
    :dedent: 4

Obviously you don't want to go through this every time you use this function so
write a wrapper function containing the above. Whilst you're at it, you can
incorporate some type normalising.

.. literalinclude:: ../../demos/multi-output/multi-output.py
    :pyobject: range_of

Now you can almost forget that this function is implemented in C::

    >>> range_of([6, 9, 3, 13.5, 8.7, -4])
    (-4., 13.5)
