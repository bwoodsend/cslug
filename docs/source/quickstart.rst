Basics
======

This tutorial assumes you have |cslug| and |gcc| installed and ready. If that is
not the case then first refer to the :ref:`Installation` guide.

Throughout these mini-tutorials we will use the convention of yellow background
code-blocks for Python and blue for C. We will also assume, for convenience,
that all files are in the current working directory unless indicated otherwise.


Hello cslug
-----------

Typically, we write C source code in its own ``.c`` file but for the purposes of
getting started we'll lazily embed the C source into our Python code using
:class:`io.StringIO`.

.. code-block:: python

    import io
    from cslug import CSlug

    slug = CSlug("my-first-slug", io.StringIO("""
        int add_1(int x) {
            return x + 1;
        }
    """))

::

    >>> slug.dll.add_1(10)
    11

Ta-da! If instead of 11 you got a :class:`cslug.exceptions.NoGccError` then
please go back to the :ref:`installation <Installation>` section to setup your C
compiler.

Let's talk through what just happened. |cslug| should have:

* Compiled a |shared library| called **my-first-dll-[...]** in your current
  working directory (where `[...]` depends on your OS). This library contains a
  single function called ``add_1()``.
* Extracted type information from our C source code. Namely: ``add_1()`` takes
  one ``int`` input and returns an ``int`` output.
* Loaded said shared library using :mod:`ctypes` (accessible via :attr:`slug.dll
  <cslug.CSlug.dll>`) and set the type information for the functions it
  contains.

Finally, ``print(slug.dll.add_1(10))`` will call our C function ``add_1()``
on ``10`` and print the answer.

.. note::

    C doesn't give a wet-slap about indentation so there is no need
    :func:`textwrap.dedent`-ify embedded C source code.


Making slugs
------------

Everything in |cslug| revolves around the :class:`cslug.CSlug` class which is
responsible for compiling your code and loading the output via :mod:`ctypes`. It
takes one output name, and an arbitrary number of source files.

.. code-block:: python

    from cslug import CSlug
    CSlug("output", "input.c")

Note the lack of a suffix for the output - this is because the suffix is
platform dependent and should therefore not be hard-coded.

For slugs containing just one source file you may specify only the source file
and output filename will default to the same name with the ``.c`` stripped.
i.e::

    CSlug("kangaroo.c")

is equivalent to::

    CSlug("kangaroo", "kangaroo.c")

A :class:`~cslug.CSlug` can take multiple source files (provided there are no
name collisions) and will merge them into one |shared library|. ::

    CSlug("some-library", "file1.c", "file2.c")

However, if you want to use functions from one file in the other, then you will
need a :ref:`header file <Headers -- Working with Multiple Files>`.

Compiling and Recompiling
-------------------------

|cslug| compiles implicitly only if any of its output files don't already exist.
To invoke a recompile use :meth:`slug.make() <cslug.CSlug.make>`.

.. code-block:: python

    slug.make()

If your source code is C file then just modify it, save it and call make - no
need to create a new :class:`~cslug.CSlug`. If you're using
:class:`io.StringIO`\ s as source files you can edit a source like below,
although it's generally easier either to create a new slug or to start putting C
code into dedicated ``.c`` files.

.. code-block:: python

    # Rewrite an `io.StringIO()` source.
    slug.sources[0] = io.StringIO("New C code")
    # Recompile the changes.
    slug.make()


Current Working Dir Independence
--------------------------------

The examples in these tutorials assume that your current working directory is
the same as the folder your Python and C code is in. This is OK for
experimentation but shouldn't be relied upon generally or your code will raise
:class:`FileNotFoundError`\ s as soon as you take it out of the safety bubble of
your favourite IDE. Instead the usual behaviour is to locate files relative to
your Python code's location (typically using ``__file__``)::

    from pathlib import Path
    from cslug import CSlug

    HERE = Path(__file__).resolve().parent
    slug = CSlug(HERE / "name", HERE / "c-code.c")

This gets pretty darn clunky so |cslug| provides an :func:`~cslug.anchor`
function to do it for you. The above can be rewritten as::

    from cslug import cslug, anchor
    slug = CSlug(anchor("name"), anchor("c-code.c"))

But, to avoid having to write :func:`~cslug.anchor` over and over, it takes
multiple arguments. The above can also be rewritten as::

    slug = CSlug(*anchor("name", "c-code.c"))

:class:`~cslug.CSlug` automatically flattens iterables of arguments so the ``*``
may be omitted::

    slug = CSlug(anchor("name", "c-code.c"))

You may specify paths rather than just filenames if your Python, C and binary
files are in different places. ::

    slug = CSlug(anchor("bin/name", "src/c-code.c"))

.. note::

    The underlying C code beneath :class:`ctypes.CDLL` is hard-coded to read
    from a true file. This means that any non pure Python package is
    automatically not zip-safe. There is therefore no advantage to using
    :func:`pkgutil.get_data` or any of its relatives.

