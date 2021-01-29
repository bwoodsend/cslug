=========================
Packaging with setuptools
=========================

.. automodule:: cslug.building
    :no-members:
    :noindex:


Quick setup
-----------

For the short way to setup your package you may use the following recipe (note
all steps are mandatory). Some of these steps are a little drastic so I
recommend you make a backup, or a git commit, so you can easily fix any mess
you make:

* Copy this :ref:`MANIFEST.in <Packaging Demo: MANIFEST.in>` into the root of
  your project (or merge with yours if you already have one).

* Similarly, copy/merge this :ref:`pyproject.toml
  <Packaging Demo: pyproject.toml>`.

* Add all your dependencies to the *[build-system] requires* list in the
  *pyproject.toml* (keep the current contents of that list). If you already
  specify your dependencies elsewhere remove them.

* Copy the following lines of :ref:`setup.py <Packaging Demo: setup.py>` into
  your *setup.py* (replacing ``contains_slugs`` with the name of your package).

.. literalinclude:: ../../packaging/contains-slugs/setup.py
    :start-at: from cslug
    :end-at: )

.. literalinclude:: ../../packaging/contains-slugs/setup.py
    :start-after: packages=

* Edit the ``"build": build_slugs("contains_slugs:deep_thought"),`` line in the
  *setup.py*, replace ``"contains_slugs:deep_thought"`` with the names of every
  :class:`cslug.CSlug` in your package (see :func:`~cslug.building.make` for
  the name format).

For the *why* and the *how to customise it*, see the rest of this page.


contains-slugs
--------------

Throughout this document we'll be using the ``contains_slugs`` package as an
example. It's contents in full are below:

 .. toctree::

    MANIFEST.in <stubs/packaging/MANIFEST.in.rst>
    README.md <stubs/packaging/README.md.rst>
    setup.py <stubs/packaging/setup.py.rst>
    pyproject.toml <stubs/packaging/pyproject.toml.rst>
    contains_slugs/__init__.py <stubs/packaging/contains_slugs/__init__.py.rst>
    contains_slugs/deep-thought.c <stubs/packaging/contains_slugs/deep-thought.c.rst>


We'll start with the :ref:`setup.py<Packaging Demo: setup.py>`. Using a
setuptools *setup.py* is currently the only supported way to use |cslug|. There
is no way to use purely a *setup.cfg* or *pyproject.toml* or any of the
alternatives to setuptools.

Apart from the |cslug| imports, the following lines are just generic *setup.py*
and should already be familiar to you. (If it isn't, check out the `Python
packaging tutorial`_.)

.. literalinclude:: ../../packaging/contains-slugs/setup.py
    :end-at: packages=


Compile on ``setup.py build``.
------------------------------

Whilst you rarely use it directly, ``setup.py build`` is called implicitly
whenever you:

* ``pip install .`` or ``pip install -e .``.
* ``python setup.py bdist_wheel`` or ``pip wheel .`` but not
  ``python setup.py sdist``.
* ``pip install /path/to/source/distribution.tar.gz`` but not
  ``pip install /path/to/binary/distribution.whl``.

You should hook ``setup.py build`` to also call :func:`cslug.CSlug.make` on
every :class:`cslug.CSlug`. We will do this by indirectly calling
:func:`cslug.building.make`. To attach our own code to the ``setup.py build``
command we must overload the ``run()`` method of
:class:`!distutils.command.build.build`. :func:`cslug.building.build_slugs` does
exactly this. i.e. creates a subclass adding :func:`~cslug.building.make` to the
``run()`` method.

So finally, to create and register this custom build class, add the following
option::

    setup(
        ...
        cmdclass={
            "build": build_slugs("contains_slugs:deep_thought"),
        },
    )

See :func:`~cslug.building.make` for how the argument(s) to
:class:`~cslug.building.build_slugs` should be formatted.

With this set up, you can now (re)compile all |cslug| components in a project
with:

.. code-block:: shell

    python setup.py build


Specify build-time dependencies
-------------------------------

By putting a |cslug| import in our *setup.py* we've made |cslug| a build time
dependency. And, because you need to import your project just to compile any
|cslug| components, most or all of your run-time dependencies are now also build
time dependencies.

The ability to specify build time dependencies is introduced by :pep:`518`. You
require a *pyproject.toml* (a *setup.cfg* is not accepted).

If you don't like that your requirements are duplicated you may use
:func:`~cslug.building.copy_requirements` to extract your build time
requirements and pass them to the ``install_requires`` option in your
*setup.py*::

    from cslug.building import copy_requirements

    setup(
        ...
        install_requires=copy_requirements(),
        ...
    )

If you have build time requirements that aren't runtime requirements you can
exclude them with::

    install_requires=copy_requirements(exclude=["build-time", "only", "packages"]),

setuptools, wheel and toml are excluded. If you want to include them or have
other runtime-only dependencies then append them::

    install_requires=copy_requirements() + ["toml", "some-other-library"],


.. warning::

    pip builds packages in an isolated environment which ignores your currently
    installed packages. If you forget a build requirement in the toml file, but
    you will still a :class:`ModuleNotFoundError` even if have it installed
    anyway.

.. note::

    If you find the isolated build environment is maddeningly slow you can skip
    it in pip using the ``--no-build-isolation``. But only once your sure it
    works without it.

When the build dependencies get noticed
.......................................

Build dependencies, being new, has a few holes in it. They are ignored (usually
resulting in :class:`ModuleNotFoundError`\ s) with any of the:

.. code-block:: shell

    python setup.py [bdist_wheel or install or anything else]

Using pip finds the build dependencies correctly so the solution is to the above
is to:

.. code-block:: shell

    pip install -e .

Or manually install the build dependencies before invoking any ``setup.py``
commands.

You also require modern versions of pip, setuptools and wheel. If you get
:class:`ModuleNotFoundError`\ s for packages which are in your toml, trying
upgrading those.

For sdists to work the *pyproject.toml* must be included in the sdist. See
:ref:`Data files for source distributions (sdists)`.


Data files for source distributions (sdists)
--------------------------------------------

An sdist should include source code but exclude anything |cslug|-generated. It's
also crucial that *pyproject.toml* is included or build time dependencies don't
get propagated.

This all happens in the :ref:`MANIFEST.in <Packaging Demo: MANIFEST.in>`. You
can just copy/paste this file directly into your project's root:

.. literalinclude:: ../../packaging/contains-slugs/MANIFEST.in
    :caption: MANIFEST.in


Data files for binary distributions (wheels)
--------------------------------------------

A binary distribution is already compiled meaning that it doesn't need source
code anymore. But it does need the compiled |binaries| and type jsons.

We're back to the *setup.py* again, this time using the ``package_data``
argument.

.. code-block:: python

    from cslug.building import CSLUG_SUFFIX

    setup(
        ...,
        include_package_data=False,
        package_data={
            "contains_slugs": ["*" + CSLUG_SUFFIX, "*.json"],
        },
    )

Make sure that you do not use ``include_package_data=True``. Using it causes
all files to be collected, including source and junk files, rather than only
those which are appropriate.

.. note::

    The above filter would prevent binaries for the wrong platform from being
    collected but for some unfortunate caching. If you compile for multiple
    platforms which share a filesystem, run ``python setup.py clean`` between
    each switch.


Platform specific wheel tag
---------------------------

Because a |cslug| package contains |binaries| but those binaries do not use the
Python ABI (i.e. don't include the line ``#include <Python.h>`` anywhere in the
C code), a package is platform specific but independent of Python/ABI version.
i.e. You can't compile on Linux and run on Windows but you can compile using
Python 3.8 and run on Python 3.6.

We need to tell setuptools this, otherwise it incorrectly assumes our packages
our Pure Python which confuses the hell out of pip. Unfortunately setuptools is
heavily geared towards Python extension modules and this is surprisingly fiddly.
But :class:`cslug.building.bdist_wheel` wraps it up for you. Just add it as
another command class in your *setup.py*::

    from cslug.building import bdist_wheel

    setup(
        ...
        cmdclass={
            "bdist_wheel": bdist_wheel,
        },
    )

Now on running:

.. code-block:: shell

    python setup.py bdist_wheel

you should notice that the wheel produced has the name of your operating system
in its filename.

.. note::

    Building wheels requires the wheel_ package. If you get an error saying
    wheel_ isn't installed then just ``pip install wheel``.

PyPA are pushing (albeit half-heartedly) away from direct ``python setup.py
command`` usage. To conform to this instead use ``pip wheel .`` to build wheels.

The above is slightly different in that it builds wheels for all your
dependencies too and places them in your current working directory rather than a
dedicated *dist* folder. For true equivalence use:

.. code-block:: shell

    pip wheel --wheel-dir dist --no-deps .

