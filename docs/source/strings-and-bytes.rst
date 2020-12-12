Strings and Bytes
=================

There are two ways to work with text.

1. Let :mod:`ctypes` implicitly convert your :class:`str` or :class:`bytes` to a
   |null terminated| char or wide char array before passing it a C function
   which takes ``char *`` or ``wchar_t *`` arguments. This is slower (due to the
   conversion - although :ref:`this can be cached<Caching the conversion
   overhead>`) but more straight forward.

2. Treat your text as an array, passing raw |pointers| to C. This is harder
   but much more efficient.

This page focuses on option :math:`1`. For option :math:`2` see :ref:`Buffers,
Arrays and NumPy Arrays`.


Reading strings
---------------

Passing strings from Python is easy. We demonstrate it with an equivalent to
Python's :meth:`str.count`, with the simplification that the sub-string we are
counting is only one character. If you want to work with :class:`bytes`
instead, simply replace ``wchar_t`` with ``char``.

.. literalinclude:: ../demos/strings/strings-demo.c
    :language: C
    :end-before: // ---
    :caption: strings-demo.c

Or a more C savvy person may prefer the equivalent but punchier code:

.. literalinclude:: ../demos/strings/strings-demo.c
    :language: C
    :start-after: // ---

The Python end is very no-nonsense. Let's compile the above::

    from cslug import CSlug
    slug = CSlug("strings-demo.c")

And run it::

    >>> slug.dll.count("hello", "l")
    2

OK, now that we've got it going, let's talk about the C code a bit.

Notice the types of the inputs: ``wchar_t *`` and ``wchar_t``. The former
accepts a :class:`str` of arbitrary length but the latter accepts only a single
character :class:`str`. We could have used pointers for both arguments, but
using just ``wchar_t`` adds an implicit check that our single character argument
is indeed singular::

    >>> slug.dll.count("This will break", "will")
    ctypes.ArgumentError: argument 2: <class 'TypeError'>: wrong type

You may also notice that we've avoided having to specify the string's length
anywhere. Instead we just use ``text[i] != 0;`` to tell us when to stop the for
loop. Here we are taking advantage of the fact that Python strings are |null
terminated|, so to find the end of a string we simply need to find the *NULL*
(integer 0) at the end. There is a catch to doing this though. If our string
contained nulls in it then this function would exit prematurely. By default,
Python won't allow us to make this mistake::

    >>> slug.dll.count("This sentence \x00 contains \x00 Nulls.", "a")
    ctypes.ArgumentError: argument 1: <class 'ValueError'>: embedded null character

However if we force our way through...

    >>> import ctypes
    >>> slug.dll.count(ctypes.create_unicode_buffer("One z \x00 lots of zzzzzzzz"), "z")
    1

If your string is likely to contains NULLs then pass the string length as a
separate parameter and use that to define your ``for`` loops.


Caching the conversion overhead
...............................

When you pass a :class:`str` or :class:`bytes` to C you implicitly call
:func:`ctypes.create_unicode_buffer` or :func:`ctypes.create_string_buffer`,
performing a conversion or copy, before passing the result to C. If you pass the
same string to C multiple times then this conversion is repeated redundantly. To
avoid this, do the conversion yourself. i.e. This performs a conversion twice::

    a = "Imagine that this string is a lot longer than it actually is."
    slug.dll.count(a, "x")
    slug.dll.count(a, "y")

Whereas this performs only one conversion::

    a = "Imagine that this string is a lot longer than it actually is."
    a_buffer = ctypes.create_unicode_buffer(a)
    slug.dll.count(a_buffer, "x")
    slug.dll.count(a_buffer, "y")


Writing to strings
------------------

We can write to strings inplace or to new strings in C, but it's not so
streamlined.

* In order to avoid the cacophony of memory issues that is creating and sharing
  buffers in C, strings should only be created in Python. To write a string in
  C, create an empty one of the right length then give it to C to populate.
  This unfortunately means that you must know how long your string will be
  before you write it.

* As we've seen above, strings are converted to :mod:`ctypes` character arrays
  when passed to a C function, which then gets discarded immediately, losing any
  changes the function made. To avoid this we must must do the conversion
  explicitly like in :ref:`Caching the conversion overhead`.

We'll show these in our next example: A C function which outputs the reverse of
a :class:`str`:

.. literalinclude:: ../demos/strings/reverse.c
    :language: C
    :caption: reverse.c

Notice that output string is an argument rather than a ``return`` value. This is
in accordance with complication one above. Let us compile our C code:

.. literalinclude:: ../demos/strings/reverse.py
    :start-at: import ctypes
    :end-at: slug =

And give ourselves something to reverse:

.. literalinclude:: ../demos/strings/reverse.py
    :start-at: in_ =
    :end-at: in_ =

Before using our C function, we need to make it an output to populate. Because
of complication two, this must be a :class:`ctypes.Array` instead of a generic
Python :class:`str` (although you can always try it anyway to see what happens).

.. literalinclude:: ../demos/strings/reverse.py
    :start-at: out =
    :end-at: slug.dll.reverse

::

    >>> out.value
    '.gnirts siht esreveR'
    >>> out.value == in_[::-1]
    True

Whenever you write a C function which requires weird handling in Python you
should write a wrapper function to keep the weirdness out the way.

.. literalinclude:: ../demos/strings/reverse.py
    :pyobject: reverse

::

    >>> reverse(".esu ot reisae hcum si noitcnuf sihT")
    'This function is much easier to use.'


A bytes example
---------------

.. literalinclude:: ../demos/bytes/encrypt.c
    :language: C



Null terminated or not null terminated?
---------------------------------------

.. highlight:: C

In C, strings are automatically null terminated if you define them
with::

    char string[] = "literal";

or for unicode strings::

    wchar_t string[] = L"literal";

If you specify the length of the string then any *spare* characters are nulls::

    char string[4] = "hello";  // Array too short to fit "hello", truncated to "hell" with a build warning.
    char string[5] = "hello";  // Not null terminated.
    char string[6] = "hello";  // Null terminated.
    char string[7] = "hello";  // Double null terminated.

.. highlight:: python3

Similarly in :mod:`ctypes`, both :func:`~ctypes.create_string_buffer` and
:func:`~ctypes.create_unicode_buffer` append a null if the length is
unspecified::

    >>> ctypes.create_unicode_buffer("hello")[:]
    'hello\x00'
    >>> ctypes.create_unicode_buffer("hello\x00")[:]
    'hello\x00\x00'

And set any *spare* characters to ``'\x00'`` if the length is specified::

    >>> ctypes.create_unicode_buffer("hello", 4)[:]
    ValueError: string too long
    >>> ctypes.create_unicode_buffer("hello", 5)[:]
    'hello'
    >>> ctypes.create_unicode_buffer("hello", 6)[:]
    'hello\x00'
    >>> ctypes.create_unicode_buffer("hello", 7)[:]
    'hello\x00\x00'

In any other case you should assume that they aren't unless the documentation
for a particular function you are using says it writes null-terminated strings.

.. note::

    The ``'\x00'`` character is an escape sequence (just like ``'\n'``), not a
    literal backslash followed by an x and two zeros.

        >>> len('\x00')
        1
        >>> print('invisible \x00 character')
        invisible  character

    In the unlikely event that you want to type it literally, use a double
    backslash or raw string::

        >>> print('\\x00')
        \x00
        >>> print(r'\x00')
        \x00
        >>> len('\\x00')
        4

