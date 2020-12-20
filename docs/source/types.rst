Types and Type Safety
---------------------

Shared libraries don't contain any information about the types of a function's
arguments or its return type. It doesn't even count how many arguments a
function takes - you just get seg-faults and memory errors if you get it wrong.

:mod:`ctypes` allows you to set the type information for functions (accessible via
``function.argtypes`` and ``function.restype``) but it means you have to
effectively copy and translate function prototypes from C into Python (which is
both mind-numbing and error-prone).

|cslug| tries to do the above for you by scanning your C source code for
function definitions, dumping the information into a json file with the same
name as your shared library (first argument to :meth:`~cslug.CSlug`) then
setting the type information for each function on loading the library (invoked
by accessing ``slug._dll_``). This provides some degree of implicit type safety
and casting for the basic types:

===============================   ====================================================================================
Python Type                       Equivalent C Type(s)
===============================   ====================================================================================
:class:`int`                      `int`, `short`, `long`, `unsigned`, `int16_t` (requires ``#include <stdint.h>``, etc
:class:`float`                    `float` or `double`
Single character :class:`str`     `wchar_t` (requires ``#include <stddef.h>``)
Arbitrary length :class:`str`     `wchar_t *`
Single character :class:`bytes`   `char`
Arbitrary length :class:`bytes`   `char *`
:class:`bool`                     `bool` (requires ``#include <stdbool.h>``
===============================   ====================================================================================


Type Checking
~~~~~~~~~~~~~

To see type checking in action, put the following function into ``typing.c``.

.. literalinclude:: ../demos/typing.c

Now, to compile it::

    from cslug import CSlug
    slug = CSlug("typing.c")

And run it. Floats pass in and out of C as we'd expect them to::

    >>> slug._dll_.reciprocal(2.0)
    0.5

Integers and any other type which can be safely converted to float are
automatically converted without complaint like they are in Python::

    >>> slug._dll_.reciprocal(4)
    .25
    >>> from fractions import Fraction
    >>> slug._dll_.reciprocal(Fraction(1, 3))
    3.0

But anything else gives a :class:`TypeError` as we'd expect::

    >>> slug._dll_.reciprocal("hello")
    ctypes.ArgumentError: argument 1: <class 'TypeError'>: wrong type

    >>> slug._dll_.reciprocal()
    TypeError: this function takes at least 1 argument (0 given)

To see what it's like without the safety net, remove the type information from
:meth:`!slug._dll_.reciprocal` and try calling it again::

    slug._dll_.reciprocal.restype = int  # The default return type.
    slug._dll_.reciprocal.argtypes = None  # Unknown arguments.


Pointer Types
~~~~~~~~~~~~~

Type checking for |pointers| on the other hand is very minimal. A ``wchar_t
*`` correlates to :class:`str` in Python (and is type-checked accordingly) and a
``char *`` correlates to :class:`bytes` (including :class:`bytearray` and
:class:`memoryview`). See :ref:`Strings and Bytes` for working with string
types. All other pointer types are reduced to ``void *``.
