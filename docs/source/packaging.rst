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

You rarely use it directly but ``setup.py build`` is called implicitly whenever
you:

* ``pip install .`` or ``pip install -e .``.
* ``python setup.py bdist_wheel`` or ``pip wheel .`` but not
  ``python setup.py sdist``.
* ``pip install /path/to/source/distribution.tar.gz`` but not
  ``pip install /path/to/binary/distribution.whl``.

It's recommended to hook ``setup.py build`` to also call
:func:`cslug.CSlug.make` on every :class:`cslug.CSlug`. We will do this by
indirectly calling :func:`cslug.building.make`. To attach our own code to the
``setup.py build`` command we must overload the ``run()`` method of
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

