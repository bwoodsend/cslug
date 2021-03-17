========================================
Accessing Global Variables and Constants
========================================

Neither :mod:`ctypes` nor |cslug| offer much help to access C globals (although
the latter may change if I feel motivated enough to do something about it).

If you're looking for a way to access constants from Python,
the preferred approach is to define them in Python then :ref:`pass them to C
<Sharing constants between Python and C>` using a header file.
And if you have non constant global variables then you are advised to
get rid of them - they're considered bad practice and rightly so.

If I have been unsuccessful in putting   you off yet then here's how to do it.
Throughout this page we'll use the following C code and Python setup:

.. literalinclude:: ../demos/globals/globals.c
    :language: c
    :caption: globals.c

.. literalinclude:: ../demos/globals/globals.py
    :start-at: import ctypes
    :end-at: slug =


Constants defined using :c:`const` are readable with the same method as global
variables but are obviously not writable. Anything defined using :c:`#define` is
preprocessor only, meaning that it gets refactored out early in the C
compilation process and doesn't exist in a shared library. To reset all globals
back to their defaults just close the library with :func:`slug.close
<cslug.CSlug.close>`.

An integer
----------

We'll start with ``an_int`` which is defined in C as:

.. literalinclude:: ../demos/globals/globals.c
    :language: c
    :start-at: int an_int
    :end-at: int

Variables are available as attributes of :attr:`slug.dll <cslug.CSlug.dll>` just
like functions are. Unfortunately, :mod:`ctypes` assumes everything it finds is
a function (calling this supposed function is a |seg-fault|)::

    >>> slug.dll.an_int
    <_FuncPtr object at 0x0000003084046E10>

We need to cast this function pointer into an int pointer (because ``an_int`` is
an int), then dereference it:

.. literalinclude:: ../demos/globals/globals.py
    :start-at: an_int =
    :end-at: an

This gives a :class:`ctypes.c_int`. Convert the to a Python :class:`int` with::

    >>> an_int.value
    42

And if the variable isn't declared :c:`const` then you can write to it::

    an_int.value = 13


.. warning::

    These variables are still pointers into the specific :class:`ctypes.CDLL`
    they originated from. Attempting to access the contents of a pointer after
    it's shared library has been either closed or reloaded is an instant crash::

        >>> slug.make()  # or `slug.close()`
        >>> print(an_int)
        Process finished with exit code -1073741819 (0xC0000005)

    To avoid this you may use lengthy one-liners::

        >>> slug.make()
        >>> ctypes.cast(slug.dll.an_int, ctypes.POINTER(ctypes.c_int)).contents.value
        42


Other basic types
-----------------

Accessing other non-pointer based types is almost identical to :ref:`An
integer` with the only difference being the :mod:`ctypes` class you provide to
:func:`ctypes.cast`:

.. literalinclude:: ../demos/globals/globals.c
    :language: c
    :start-at: float
    :end-at: int8

See the `ctypes types table`_ to match types. There is no protection if you get
it wrong.

.. literalinclude:: ../demos/globals/globals.py
    :start-at: a_float =
    :end-at: an_

::

    >>> a_float.value, a_double.value, an_8_bit_int.value
    (0.3333333432674408, 0.3333333333333333, 43)


String, bytes and arrays
------------------------

Accessing strings and bytes is slightly different because they are already
pointers.

.. literalinclude:: ../demos/globals/globals.c
    :language: c
    :start-at: char
    :end-at: wchar

To access them you can use:

.. literalinclude:: ../demos/globals/globals.py
    :start-at: a_byte
    :end-at: a_string

But be careful with this form. It doesn't know the lengths of these strings - it
guesses, assuming they are |null terminated| (which in this case they are
because, on defining them with :c:`char x[] = "literal"`, C appends a NULL
character). If a string isn't null terminated, memory trash characters will be
appended until a 0 is found and if a string contains other NULLs then it will
be terminated prematurely.

.. literalinclude:: ../demos/globals/globals.c
    :language: c
    :start-at: char contains
    :end-at: int

Because the above byte array contains a NULL character, it gets mistakenly
shortened::

    >>> ctypes.cast(slug.dll.contains_null, ctypes.c_char_p).value
    b'This sentence has a '

A better, albeit much longer, way is to mark it as an array of a specified
length. This approach will work for any array type as well as strings:

.. literalinclude:: ../demos/globals/globals.py
    :start-at: # Extract
    :end-at: contains_null =

This gives us a scriptable :class:`ctypes.Array` object. Not only can we see
past the NULL character in the middle but we can see that this string is also
|null terminated|::

    >>> contains_null
    <ctypes.c_char_Array_43 object at 0x00000027896043C0>
    >>> contains_null[:]
    b'This sentence has a \x00 in the middle of it.\x00'
    >>> contains_null.raw
    b'This sentence has a \x00 in the middle of it.\x00'


Setting arrays
..............

You can modify individual elements using::

    contains_null[0] = b"A"

Or series of elements (note lengths must match)::

     contains_null[:5] = b"abcde"

Or the whole array (again the length must not change)::

    contains_null[:] = contains_null[:].upper()

If you intend to set array pointer to point to a different array (definitely not
recommended) then read :ref:`Warning for Structs Containing Pointers` - the same
warnings apply here.
