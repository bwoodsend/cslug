Basics
======

This tutorial assumes you have |cslug| and |gcc| installed and ready. If that is
not the case then first refer to the :ref:`Installation` guide.

Hello cslug
-----------

Typically, we write C source code in its own ``.c`` file but for the purposes of
getting started we'll lazily embed the C source into our Python code using
:class:`io.StringIO`.

.. code-block:: python

    import io
    from cslug import CSlug

    slug = CSlug("my-first-slug", io.StringIO("""
        // Note that indentation has no effect in C so it doesn't matter if/how
        // you indent this block.
        int add_1(int x) {
            return x + 1;
        }
    """))

    print(slug.dll.add_1(10))

Ta-da! Provided nothing went pear-shaped, you should have got ``11``. If instead
you get a :class:`cslug.exceptions.NoGccError` then please return to the
:ref:`Installation` section.

Let's break down what just happened. |cslug| should have:

* Compiled a |shared library| called **my-first-dll-[...]** in your current
  working directory (where `[...]` depends on your OS). This library contains a
  single function called ``add_1()``.
* Extracted type information from our C source code. Namely: ``add_1()`` takes
  one ``int`` input and returns an ``int`` output.
* Loaded said shared library using :mod:`ctypes` (accessible via ``slug.dll``)
  and set the type information for the functions it contains.

Finally, ``print(slug.dll.add_1(10))`` will call our C function ``add_1()``
on ``10`` and print the answer (``11`` I think?).


Making slugs
------------




Compiling and Recompiling
-------------------------

|cslug| will only compile the shared library for you if it doesn't already
exist. To invoke a recompile use :meth:`slug.make() <cslug.CSlug.make>`.

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

