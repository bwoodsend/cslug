======================================
Headers -- Working with Multiple Files
======================================

Pre-waffle: What headers are for
--------------------------------

Multiple source files can included in one |shared library| just by passing
more than one source file to :class:`cslug.CSlug`. The namespace for each source
file will be merged (clashes cause a build error). If you want to be able to use
functions from one file in another file then you need a header file.

To demonstrate how to do this we'll be using the following uninspired example:

.. literalinclude:: ../demos/headers/file1.c
    :caption: file1.c
    :name: file1.c
    :language: C

.. literalinclude:: ../demos/headers/file2.c
    :caption: file2.c
    :name: file2.c
    :start-at: int uses_do_nothing(int x) {
    :language: C

This refuses to compile because there is a reference to :c:`do_nothing()` from
`file1.c` inside `file2.c` (although some compiler versions let you off with
just a warning):

.. code-block:: python

    from cslug import CSlug
    slug = CSlug("lib_nothing", "file1.c", "file2.c")
    slug.make()

To keep the compiler happy we need to put a function prototype for
:c:`do_nothing()` somewhere visible to `file2.c`. In this simple case it's enough
to just put :c:`int do_nothing(int x);` at the  top of `file2.c` but if a third
file also needed :c:`do_nothing()` then this would require duplicating the
prototype. The more general solution is to put function prototypes in a header
file which any other file can :c:`#include`.


Auto-generating header files
----------------------------

Writing header files is boring and generally devolves to copy/paste (bad).
:class:`cslug.Header` tries to do it for you. The following writes a header file
containing prototypes for every function from :ref:`file1.c` and :ref:`file2.c`.

.. code-block:: python

    from cslug import Header, CSlug
    header = Header("my-header.h", "file1.c", "file2.c")
    slug = CSlug("lib_nothing", "file1.c", "file2.c", headers=header)

Passing the header to :class:`~cslug.CSlug` means that calling
:func:`slug.make() <cslug.CSlug.make>` will implicitly call :func:`header.make()
<cslug.Header.make>` so that you still only have one `make()` command (although
you may use :func:`header.make() <cslug.Header.make>` directly or
:func:`header.write() <cslug.Header.write>` to experiment with
:class:`~cslug.Header`\ s without going through a :class:`~cslug.CSlug`).

The resulting header file looks something like:

.. code-block:: C
    :caption: my-header.h

    // -*- coding: utf-8 -*-
    // Header file generated automatically by cslug.
    // Do not modify this file directly as your changes will be overwritten.

    #ifndef MY_HEADER_H
    #define MY_HEADER_H

    // file1.c
    int do_nothing(int x);

    // file2.c
    int uses_do_nothing(int x);

    #endif

Now any file which references anything from either `file1.c` or `file2.c` need
only :c:`#include "my-header.h"`.

.. note::

    You don't need to pass header files (automatically generated or otherwise)
    to :class:`cslug.CSlug`, although there is no harm in doing so.


Sharing constants between Python and C
--------------------------------------

Header files are also a good place to put constants or enumerations where other
C files can easily see them. With |cslug|, you may define constants in Python,
using either a class from the :mod:`enum` package or just a plain dictionary,
then let :class:`cslug.Header` propagate it into a header file for you.

.. code-block:: python

    import enum
    from cslug import Header

    class ErrorCode(enum.Enum):
        OK = enum.auto()
        NOT_OK = enum.auto()
        VERY_BAD = enum.auto()
        APOCALYPSE = enum.auto()

    header = Header("constants.h", defines=ErrorCode) # defines=[ErrorCode] is also ok.

Quickly inspect using::

    >>> header.write()
    #ifndef CONSTANTS_H
    #define CONSTANTS_H

    // ErrorCode
    #define OK 1
    #define NOT_OK 2
    #define VERY_BAD 3
    #define APOCALYPSE 4

    #endif

Now any Python code can access the ``APOCALYPSE`` constant via
``ErrorCode.APOCALYPSE`` and any C code can :c:`#include "constants.h"` and use
``APOCALYPSE`` directly.

Other relatives of :class:`enum.Enum` such as :class:`enum.IntEnum` and
:class:`enum.IntFlag` as well as :class:`dict`\ s can also be passed to the
``defines=`` option. Values are cast to strings using :class:`str` then
substituted into the header as is (without surrounding quotes). If that isn't
what you want then you may need to pass a dictionary comprehension based on the
`enum.Enum.__members__
<https://docs.python.org/3/library/enum.html#supported-dunder-names>`_ attribute
instead.


Add :c:`#include`\s to generated headers
----------------------------------------

If you use types which are defined in other header files such as :c:`wchar_t`
then you need to :c:`#include` those headers to the generated header. For local
headers use::

    Header(..., includes='some-header.h')

or for system-wide ones libraries enclose with angle brackets::

    Header(..., includes='<stddef.h>')

Pass a :class:`list` if you have more than one::

    Header(..., includes=['<stddef.h>', '<stdint.h>'])

Add arbitrary code to generated headers
---------------------------------------

This is intentionally not supported. If you want custom code in an automatically
generated header then put your code in a separate file which either
`#include`\ s or is `#include`\ d by the generated one.
