=========================
Customising C Compilation
=========================

Whilst |cslug| aims to eliminate the need for configuration,
there are a few knobs for options which may be forwarded on the the C compiler.

.. note::

    The setting of these options will not trigger a recompile.
    To have any effect you must call :meth:`cslug.CSlug.make`,
    or if you set up :ref:`setuptools integration <Packaging
    with setuptools>`,
    re-run ``python setup.py build``.


Select a C compiler
-------------------

A compiler may be selected using the ``CC`` environment variable.
This may be:

1. A name e.g. ``clang`` which will be searched for in ``PATH``.
2. A relative path to a compiler executable (rare).
   If it in the current working directory it should have a ``./`` prefix to
   disambiguate from form 1.
3. A full path to a compiler executable.

This feature is intended to be used after setting up
:ref:`setuptools integration <Packaging with setuptools>`
to temporarily switch to an alternative compiler.
For example to recompile a project using the TinyCC_ (aka ``tcc``) compiler run:

On Unix (Linux, macOS, FreeBSD and any Unix emulator such as MSYS2)::

    CC=tcc python setup.py build

Or for Windows::

    set CC=tcc
    python setup.py build

Whilst you can either set ``CC`` permanently, or pin it in Python code using::

    os.environ["CC"] = "tcc"

This is generally indicative of a poorly setup environment and is not
recommended.

.. _TinyCC: https://bellard.org/tcc/


Add compiler flags
------------------

|cslug| supports two ways to add compiler flags.

1. Using the **flags** option of :class:`cslug.CSlug`.
2. Via the ``CFLAGS``  environment variable (or its legacy alias ``CC_FLAGS``).

Option :math:`1` is the preferred long term approach.
``CFLAGS`` may be used to temporarily trial new options.

.. versionadded:: 0.3.0

    The ``CC_FLAGS`` environment variable.

.. versionadded:: 1.0.0

    The ``CFLAGS`` alias for ``CC_FLAGS``.


Select warnings
...............

Options may be used to silence a particular compiler warning that you are not
interested in.
For example, if you want to divide by zero without being warned against it::

    slug = CSlug("file.c", flags=["-Wno-div-by-zero"])

See ``gcc --help=warnings`` for a complete list of warning names.


Extra :c:`#include` paths
.........................

If you use a 3\ :superscript:`rd` party C library in your own C code then you
will likely need to add **the folder containing that library** to your
compiler's search path using the ``-I`` option::

    slug = CSlug("your-code.c", flags=["-I", "/path/to/extra/library"])


Minimum OSX version
-------------------

To compile on a new macOS version then run on an older one requires setting the
macOS deployment target (``-mmacosx-version-min=`` compiler option) to whatever
the oldest version is that you wish to support.
By default, |cslug| sets this to |mmacosx_version_min| which is the same as the
oldest version of Python that |cslug| supports, so in theory you should never
have reason to lower it.
You may however need to raise it if your compiler lacks the SDKs for older
versions.
Do this by setting the ``MACOSX_DEPLOYMENT_TARGET`` environment variable
(assuming that you set up :ref:`setuptools integration <Packaging with
setuptools>`)
::

    MACOSX_DEPLOYMENT_TARGET=10.10 python setup.py build

.. versionadded:: 0.3.0

    The ``MACOS_DEPLOYMENT_TARGET`` environment variable.

.. versionadded:: 1.0.0

    The ``MACOSX_DEPLOYMENT_TARGET`` alias for
    ``MACOS_DEPLOYMENT_TARGET``.


Architectures for macOS
-----------------------

Newer macOS machines have switched from ``x86_64`` to ``arm64``.
To support both you need to compile for both.
You can do this either by compiling ``x86_64`` and ``arm64`` binaries separately
and distributing them separately as you would for other operating systems
or by compiling a single *fat* binary which contains both ``x86_64`` and
``arm64`` code in one file.
It's up to you which path you choose.
Python itself has chosen the *fat* route but most packages are opting for
separate wheels for each architecture.

Unless you habitually keep everything up to date, you will likely need to
upgrade your environment.
Compiling for ARM requires a macOS version :math:`\ge 10.15`
and the XCode command line tools with version :math:`\ge 12.2`.
If you lack these requirements, you will typically get some strange compiler
errors somewhere deep in the macOS SDK when compiling ``arm64`` slices.

Architecture selection is done via the ``MACOSX_ARCHITECTURE`` environment
variable. Again assuming that you set up :ref:`setuptools integration <Packaging
with setuptools>`:

* Build an ``arm64`` wheel::

    MACOSX_ARCHITECTURE=arm64 python setup.py bdist_wheel

* Build an ``x86_64`` wheel::

    MACOSX_ARCHITECTURE=x86_64 python setup.py bdist_wheel

* Build a dual ``universal2`` wheel::

    MACOSX_ARCHITECTURE=universal2 python setup.py bdist_wheel

You can verify a wheel's architecture simply by looking at its filename.
It should contain either ``arm64``, ``x86_64`` or ``universal2`` in it.
To verify a single binary's architecture, use macOS's builtin ``lipo`` tool.

.. code-block:: shell

    $ lipo -archs some-slug-Darwin-64bit.so
    x86_64 arm64

.. versionadded:: v0.5.0

    The ``MACOS_ARCHITECTURE`` environment variable.

.. versionadded:: v1.0.0

    The ``MACOSX_ARCHITECTURE`` alias for ``MACOS_DEPLOYMENT_TARGET``.
