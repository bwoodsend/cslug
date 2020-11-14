=================
Welcome to cslug!
=================

.. image::
    https://img.shields.io/badge/
    python-%203.6%20%7C%203.7%20%7C%203.8%20%7C%203.9%20-blue.svg

Quick and painless wrapping C code into Python.

* Free software: MIT license
* Documentation: https://cslug.readthedocs.io.
* Source: https://github.com/bwoodsend/cslug
* Releases: https://github.com/bwoodsend/cslug/releases

The |cslug| package provides a thin layer on top of the built-in ctypes_
library, making it easy to load functions and structures from C into Python.

Alternatives
------------

Mixing C with Python is nothing new - there are plenty of other ways. A nice
comparison of the various methods can be found `here
<https://intermediate-and-advanced-software-carpentry.readthedocs.io/en/latest/c++-wrapping.html>`_.
cslug aims to be the simplest although it certainly isn't the most flexible.


Installation
------------

|cslug| requires gcc_ to compile your C code. If you're on Linux you probably
already have it. Other OS users should get it with mingw_. To check you have it
run the following in terminal::

    gcc -v

Install cslug itself with the usual::

    pip install cslug

This package is very much in its beta-stages and its API will likely move
around. Please don't assume forward compatibility - pick a version you like and
pin it in a ``requirements.txt``.


Quickstart
----------

Hello cslug
~~~~~~~~~~~

Typically, we write C source code in its own ``.c`` file but for the purposes of
getting started we'll be lazy embed the C source into our Python code using
:meth:`io.StringIO`.

.. code-block:: python

    import io
    from cslug import CSlug

    slug = CSlug("my-first-slug", io.StringIO("""
        // Note that indentation has no effect in C.
        int add_1(int x) {
            return x + 1;
        }
    """))

    print(slug.dll.add_1(10))

If you get a :class:`NoGCCError` then please return to the
:ref:`Installation` section. Provided nothing went pear-shaped, |cslug| should
have:

* Compiled a shared library called ``my-first-dll-[...]`` in your current
  working directory (where ``[...]`` depends on your OS) containing a single
  function ``add_1()``.
* Extracted type information from our C source code. Namely: ``add_1()`` takes
  one :class:`int` input and returns an :class:`int` output.
* Loaded said shared library using ctypes_ (accessible via ``slug.dll``) and
  set the type information for the functions it contains.

The finally ``print(slug.dll.add_1(10))`` will call our C function ``add_1()``
on ``10`` and print the answer (``11``).

Type Safety
...........

By setting the type information for each function for you (accessible via
``slug.dll.add_1.argtypes`` and ``slug.dll.add_1.restype``), |cslug| provides
some degree of implicit type safety for basic types such as ``int``\ s (and
its derivatives such as ``short int``), ``float``\ s, ``str``\s and ``bytes``.


Modifying the C code
~~~~~~~~~~~~~~~~~~~~

|cslug| will only compile the shared library for you if it doesn't already
exist. To recompile use :meth:`CSlug.make`.

.. code-block:: python

    slug.sources.append()


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

.. _ctypes: https://docs.python.org/3.9/library/ctypes.html
.. _mingw: http://mingw-w64.org/doku.php/download
.. _gcc: https://gcc.gnu.org/
.. |cslug| replace:: **cslug**
