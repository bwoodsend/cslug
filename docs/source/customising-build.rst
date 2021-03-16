=========================
Customising C Compilation
=========================

Whilst |cslug| aims to eliminate the need for configuration,
there are a few knobs for options which may be forwarded on the the C compiler.

.. note::

    The setting of these options will not trigger a recompile.
    To have any effect you must call :meth:`cslug.CSlug.make`,
    or if you set up `setuptools integration <Packaging with setuptools>`_,
    re-run ``python setup.py build``.


Select a C compiler
-------------------

A compiler may be selected using the ``CC`` environment variable.
This may be:

1. A name e.g. ``clang`` which will be searched for in ``PATH``.
2. A relative path to a compiler executable (rare).
   If it in the current working directory it should have a `./` prefix to
   disambiguate from form 1.
3. A full path to a compiler executable.

This feature is intended to be used after setting up `setuptools integration
<Packaging with setuptools>`_ to temporarily switch to an alternative compiler.
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


Minimum OSX version
-------------------

To compile on a new macOS version then run on an older one requires setting the
macOS deployment target (``-macos-version-min`` compiler option) to whatever
the oldest version is that you wish to support.
By default, |cslug| sets this to |macos_version_min| which is the same as the
oldest version of Python that |cslug| supports, so in theory you should never
have reason to lower it.
You may however need to raise it if your compiler lacks the SDKs for older
versions.
Do this by setting the ``MACOS_DEPLOYMENT_TARGET`` environment variable
(assuming that you set up `setuptools integration <Packaging with setuptools>`_)
::

    MACOS_DEPLOYMENT_TARGET=10.10 python setup.py build

.. versionadded:: 0.3.0
