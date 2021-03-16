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

Using ctypes driven wrapping has both advantages and disadvantages over Python
extension modules and tools that write them (such as Cython_).


Advantages
..........

* C code can be just plain high school level C.
  Even a hello world Python extension module is some 40 lines of incomprehensible
  macros.
  This does not apply to Cython.
* Binaries are not linked against Python and are therefore not tied to a
  specific Python version.
  A Python extension module needs to be recompiled for every minor version of
  Python (3.6, 3.7, 3.8, 3.9) and for every platform (Windows, macOS, Linux)
  whereas a **cslug** binary need only be compiled for every platform.
* You can use virtually any C compiler.
  Python extension modules must be built with clang_ on macOS and MSVC on
  Windows.
* File sizes of binaries are very small.
  1000 lines of C code equates to about 20KB of binary on Linux.


Disadvantages
.............

* The surrounding Python code is less automated. A Python extension module looks
  and feels like a native Python module out the box whereas a small wrapper
  function is generally required for ctypes.
* You can't use native Python types such as ``list`` or ``dict`` within C code.
  However, using such types will generally reduce performance down to near pure
  Python levels anyway.
* You can't use C++.


Shared Caveats
..............

Before you commit yourself to any non Pure-Python you should bear in mind:

* You should ship wheels for every platform you wish to support.
  Otherwise, users of your code will have to install a C compiler to run it.
  This means that you either need access to all platforms, or you will have to
  setup Continuous Integration to build you package on a cloud server.
* Linux wheels must be built on a manylinux Docker image in order to be
  compatible with all distributions of Linux.
* Unless your users have the relevant security thrice disabled, uninstalled,
  blocked and scraped off the hard drive,
  recent macOS will block or delete any binary file you produce
  unless you throw them some money and get it code-signed.


Supported Compilers
-------------------

======== ===== ======= ===== ======= ============
Compiler Linux Windows macOS FreeBSD Cygwin/msys2
======== ===== ======= ===== ======= ============
gcc_     ✓     ✓       ✓     ✓       ✓
clang_   ✓     ✗       ✓     ✓       ✗
MSVC     ✗     ✗       ✗     ✗       ✗
TinyCC_  ✓     ✓       ✗     ✗       ✗
======== ===== ======= ===== ======= ============


Installation
------------

**cslug** requires a C compiler to compile C code.
Its favourite compiler is gcc_.
If you're on Linux you probably already have it.
If you are on another OS then you should get it with mingw_.
To check you have it run the following in terminal::

    gcc -v

.. note::

    gcc_ is a build time dependency only. If you provide wheels for a package
    that contain binaries built with **cslug**, then your users will not need a
    compiler; only if they try to build your package from source.

By default, **cslug** will use gcc_ if it can find it. On macOS or FreeBSD it
will switch to clang_ if **gcc** is unavailable.
To use any other supported compiler, **cslug** respects the ``CC`` environment
variable.
Set it to the name or full path of your alternative compiler.

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

:emphasis:`Hall of fame for contributions to cslug`.

* .. figure:: https://raw.githubusercontent.com/bwoodsend/cslug/master/docs/source/icons/jetbrains.svg
    :target: JetBrains_
    :height: 75px

    Huge shout out to JetBrains_ for PyCharm_ and for providing their full range
    of products `free to open source developers
    <https://www.jetbrains.com/community/opensource/#support>`_.
    (The ability to run Python from inside a docker image with completion,
    debugging, and all the other bells and whistles has been a big help to this
    project.)


* .. figure:: https://raw.githubusercontent.com/cookiecutter/cookiecutter/3ac078356adf5a1a72042dfe72ebfa4a9cd5ef38/logo/cookiecutter_medium.png
    :target: Cookiecutter_
    :height: 75px

    This initial creation of this package was sped up considerably by
    Cookiecutter_ and a fork of the `audreyr/cookiecutter-pypackage`_ project
    template.


.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

.. _JetBrains: https://jb.gg/OpenSource
.. _PyCharm: https://www.jetbrains.com/pycharm/
.. _ctypes: https://docs.python.org/3.9/library/ctypes.html
.. _mingw: http://mingw-w64.org/doku.php/download
.. _gcc: https://gcc.gnu.org/
.. _TinyCC: https://bellard.org/tcc/
.. _clang: https://clang.llvm.org/
.. _`pcc`: http://pcc.ludd.ltu.se/
.. _`Cython`: https://cython.readthedocs.io/en/latest/index.html
