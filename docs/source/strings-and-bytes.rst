Strings and Bytes
=================


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

