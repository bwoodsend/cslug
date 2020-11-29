=================
Welcome to cslug!
=================

.. image::
    https://img.shields.io/badge/
    Python-%203.6%20%7C%203.7%20%7C%203.8%20%7C%203.9%20-%2326543A.svg

Quick and painless wrapping C code into Python.

* Free software: MIT license
* Documentation: https://cslug.readthedocs.io.
* Source: https://github.com/bwoodsend/cslug
* Releases: https://github.com/bwoodsend/cslug/releases

The **cslug** package provides a thin layer on top of the built-in ctypes_
library, making it easier to load functions and structures from C into Python.

Alternatives
------------

Mixing C with Python is nothing new - there are plenty of other ways. A nice
comparison of the various methods can be found `here
<https://intermediate-and-advanced-software-carpentry.readthedocs.io/en/latest/c++-wrapping.html>`_.
**cslug** aims to be the simplest although it certainly isn't the most flexible.


Installation
------------

**cslug** requires gcc_ to compile C code. If you're on Linux you probably
already have it but if you are on another OS then you should get it with
mingw_. To check you have it run the following in terminal::

    gcc -v

.. note::

    gcc_ is a build time dependency only. If you provide wheels for a package
    that contain binaries built with **cslug**, then your users will not need a
    compiler; only if they try to build your package from source.

To install **cslug** itself use the usual::

    pip install cslug

This package is very much in its beta-stages and its API will likely move
around. Please don't assume forward compatibility - pick a version you like and
pin it in a ``requirements.txt``.


Quickstart
----------

Check out our `quickstart page on readthedocs
<https://cslug.readthedocs.io/en/latest/quickstart.html>`_ to get started.


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

.. _ctypes: https://docs.python.org/3.9/library/ctypes.html
.. _mingw: http://mingw-w64.org/doku.php/download
.. _gcc: https://gcc.gnu.org/
