=================
Welcome to cslug!
=================

∘
`MIT license <https://github.com/bwoodsend/cslug/blob/master/LICENSE>`_
∘
`PyPI <https://pypi.org/project/cslug>`_
∘
`Documentation <https://cslug.readthedocs.io/>`_
∘
`Source Code <https://github.com/bwoodsend/cslug>`_
∘
`Raise Bugs <https://github.com/bwoodsend/cslug/issues>`_
∘
`Support <https://github.com/bwoodsend/cslug/discussions>`_

Quick and painless wrapping C code into Python.
The **cslug** package provides a thin layer on top of the built-in ctypes_
library, making it easier to load functions and structures from C into Python.

.. code-block:: c

    // hello-cslug.c

    int add_1(int x) {
      return x + 1;
    }

    double times_2(double x) {
      return x * 2.0;
    }

.. code-block:: python

    >>> from cslug import CSlug
    >>> slug = CSlug("hello-cslug.c")
    >>> slug.dll.add_1(12)
    13
    >>> slug.dll.times_2(-5)
    -10.0


Alternatives
------------

Mixing C with Python is nothing new - there are plenty of other ways.
The most common way is to write Python extension modules.
A nice comparison of the various methods can be found `here
<https://intermediate-and-advanced-software-carpentry.readthedocs.io/en/latest/c++-wrapping.html>`_.
**cslug** aims to be the simplest although it certainly isn't the most flexible.

Using ctypes driven wrapping has both advantages and disadvantages over Python
extension modules and tools that write them (such as Cython_).


Advantages
..........

* C code can be just plain high school level C.
  Even a hello world Python extension module is some 40 lines of hairy looking
  macros.
* Binaries are not linked against Python and are therefore not tied to a
  specific Python version.
  A Python extension module needs to be recompiled for every minor version of
  Python (3.8, 3.9, 3.10, 3.11) and for every platform (Windows, macOS, Linux)
  whereas a **cslug** binary need only be compiled for every platform.
* You can use virtually any C compiler.
  Python extension modules must be built with clang_ on macOS and MSVC on
  Windows.
  The real advantage of this is that you can use the same compiler on all
  platforms making them considerably more homogonuos and thus greatly reducing
  your chances of having to debug an issue present only on your least favourite
  platform.
* File sizes of binaries are very small.
  1000 lines of C code equates to about 20KB of binary on Linux.
  Python extension modules are typically several times larger and
  a bare-bones Cython-ised ``import numpy`` extension is several MBs.


Disadvantages
.............

* The surrounding Python code is less automated. A Python extension module looks
  and feels like a native Python module out the box complete with function
  metadata and docstrings whereas a small wrapper function is generally required
  for ctypes.
* You can't use native Python types such as ``list`` or ``dict`` within C code.
  Using such types will generally reduce performance down to near pure
  Python levels anyway so this is a small loss in practice.
* You can't use C++.


Shared Caveats
..............

Before you commit yourself to any non Pure-Python you should bear in mind that:

* You'll need to ship wheels for every platform you wish to support
  otherwise users of your code will have to install a C compiler to run it.
  This means that you either need access to all platforms, or you will have to
  setup Continuous Integration to build you package on the cloud.
  Linux users can get around this by using Vagrant_.
* Linux wheels must be built on a manylinux_ Docker image in order to be
  widely compatible with most distributions of Linux.
* Recent macOS versions will typically block or delete any binary file you
  produce unless you either purchase a codesign license
  or your software becomes famous enough to be whitelisted for you by Apple
  (binaries uploaded to PyPI seem to be exempt automatically).
  Windows users face a similar, albeit lesser, problem with Microsoft Defender.


Supported Compilers
-------------------

The following OS/compiler combinations are fully supported and tested routinely.

============ ==== ====== ==== ======= ==========
Platform     gcc_ clang_ MSVC TinyCC_ PGCC_ \*\*
============ ==== ====== ==== ======= ==========
Linux        ✓    ✓      ✗    ✓       ✓
Windows      ✓    ✓      ✗    ✓       ✗
macOS        ✓    ✓      ✗    ✗       ✗
FreeBSD      ✓    ✓      ✗    ✗       ✗
OpenBSD      ✓    ✓      ✗    ✗       ✗
NetBSD       ✓    ✓      ✗    ✗       ✗
DragonFlyBSD ✓    ✓      ✗    ✗       ✗
Cygwin/msys2 ✓    ✓      ✗    ✗       ✗
Android*     ✗    ✓      ✗    ✗       ✗
Omnios       ✓    ✓      ✗    ✗       ✗
Solaris      ✓    ✓      ✗    ✗       ✗
============ ==== ====== ==== ======= ==========

\* Using Termux_.
\*\* Installable as part of the `NVIDIA HPC SDK`_.

Installation
------------

**cslug** requires a C compiler to compile C code.
Its favourite compiler is gcc_.
Linux distributions typically come with it preinstalled.
If you are on another OS or just don't have it then you should get it with
mingw-w64_.
Windows users are recommended to download WinLibs_ without
``LLVM/Clang/LLD/LLDB`` (although **cslug** works with ``clang`` too)
and add its ``mingw64/bin`` directory to ``PATH``.

Check that you have it set up by running the following in a terminal::

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

Install **cslug** itself with the usual::

    pip install cslug

Whilst **cslug** is still in its 0.x versions, breaking changes may occur on
minor version increments.
Please don't assume forward compatibility - pick a version you like and
pin it in a ``requirements.txt``.
Inspect the `changelog`_ for anything that may break your code.


Quickstart
----------

Check out our `quickstart page on readthedocs
<https://cslug.readthedocs.io/en/latest/quickstart.html>`_ to get started.

.. _changelog: https://cslug.readthedocs.io/en/latest/history.html
.. _ctypes: https://docs.python.org/3/library/ctypes.html
.. _mingw-w64: https://www.mingw-w64.org/downloads/
.. _gcc: https://gcc.gnu.org/
.. _TinyCC: https://bellard.org/tcc/
.. _clang: https://clang.llvm.org/
.. _`pcc`: http://pcc.ludd.ltu.se/
.. _`Cython`: https://cython.readthedocs.io/en/latest/index.html
.. _Vagrant: https://github.com/hashicorp/vagrant
.. _manylinux: https://github.com/pypa/manylinux/tree/manylinux1
.. _Termux: https://termux.com/
.. _WinLibs: https://www.winlibs.com/
.. _PGCC: https://docs.nvidia.com/hpc-sdk/pgi-compilers/20.4/x86/pgi-ref-guide/index.htm
.. _`NVIDIA HPC SDK`: https://developer.nvidia.com/hpc-sdk
