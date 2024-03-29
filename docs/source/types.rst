Types and Type Safety
---------------------

Shared libraries don't contain any information about the types of a function's
arguments or its return type. It doesn't even count how many arguments a
function takes - you just get |seg-faults| and memory errors if you get it wrong.

:mod:`ctypes` allows you to set the type information for functions (accessible via
``function.argtypes`` and ``function.restype``) but it means you have to
effectively copy and translate function prototypes from C into Python (which is
both mind-numbing and error-prone).

|cslug| automates the above by scanning your C source code for
function definitions, dumping the information into a json file with the same
name as your shared library (first argument to :class:`~cslug.CSlug`) then
setting the type information for each function on loading the library (invoked
by accessing ``slug.dll``). This provides some degree of implicit type safety
and casting for the basic types:

========================   ======================================================================================
Python Type                Equivalent C Type(s)
========================   ======================================================================================
`int`                      ``int``, ``short``, ``long``, ``unsigned``, ``int16_t`` (requires :c:`#include <stdint.h>`), etc
`float`                    ``float`` or ``double``
Single character `str`     ``wchar_t`` (requires :c:`#include <stddef.h>`)
Arbitrary length `str`     ``wchar_t *``
Single character `bytes`   ``char``
Arbitrary length `bytes`   ``char *``
`bool`                     ``bool`` (requires :c:`#include <stdbool.h>`)
========================   ======================================================================================


Type Checking
~~~~~~~~~~~~~

You don't need to do anything to enable type checking - it's automatic.
The rest of this page is purely to see type checking in action.
Put the following function into ``typing.c``.

.. literalinclude:: ../demos/typing.c
    :language: C

Now, to compile it::

    from cslug import CSlug
    slug = CSlug("typing.c")

And run it. Floats pass in and out of C as we'd expect them to::

    >>> slug.dll.reciprocal(2.0)
    0.5

Integers and any other type which can be safely converted to float are
automatically converted without complaint like they are in Python::

    >>> slug.dll.reciprocal(4)
    .25
    >>> from fractions import Fraction
    >>> slug.dll.reciprocal(Fraction(1, 3))
    3.0

But anything else gives a :class:`TypeError` as we'd expect::

    >>> slug.dll.reciprocal("hello")
    ctypes.ArgumentError: argument 1: <class 'TypeError'>: wrong type

    >>> slug.dll.reciprocal()
    TypeError: this function takes at least 1 argument (0 given)

To see what it's like without the safety net, remove the type information from
:meth:`!slug.dll.reciprocal` and try calling it again::

    slug.dll.reciprocal.restype = int  # The default return type.
    slug.dll.reciprocal.argtypes = None  # Unknown arguments.


Pointer Types
~~~~~~~~~~~~~

Type checking for |pointers| on the other hand is very minimal. A :c:`wchar_t
*` correlates to :class:`str` in Python (and is type-checked accordingly) and a
:c:`char *` correlates to :class:`bytes` (including :class:`bytearray` and
:class:`memoryview`). See :ref:`Strings and Bytes` for working with string
types. All other pointer types are reduced to :c:`void *`.
