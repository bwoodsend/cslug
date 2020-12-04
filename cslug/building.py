# -*- coding: utf-8 -*-
r"""
Tools for integrating with :std:doc:`setuptools`.

Integration with :std:doc:`setuptools` is a somewhat messy affair. By putting a
:class:`cslug.CSlug` in a package, we now have to coerce our package setup to do
the following 5 things:

#. (Re)build all :class:`cslug.CSlug`\ s on ``setup.py build``.
#. Include C source code in sdists but exclude them from wheels.
#. Include |cslug| type jsons and |binaries| of the correct OS in wheels but
   exclude them from sdists.
#. Mark |cslug| as a build-time dependency to be installed before trying to run
   ``setup.py build``.
#. Mark wheels as platform dependent but Python version independent.

Wrappers around :std:doc:`setuptools` components to help build and include
|cslug| binaries in sdists and wheels.

 """

from distutils.command.build import build as _build
from cslug._cdll import SUFFIX as CSLUG_SUFFIX


def make(*names):
    r"""Import and call :func:`slug.make <cslug.CSlug.make>`.

    :param names: Names of :class:`~cslug.CSlug`\ s.
    :type names: str

    The syntax for a :class:`~cslug.CSlug` name is "module_name:attribute_name".
    For example, ``make("foo.bar:pop.my_slug")`` is equivalent to::

        from foo.bar import pop
        pop.my_slug.make()

    Of course, ``foo.bar`` must be importable for this to work.

    Multiple strings may be passed as arguments - this is just a lazy for loop.
    ``make("foo.slug", "bar.other_slug")`` is equivalent to::

        make("foo.slug")
        make("bar.other_slug")

    """
    import importlib
    import operator

    for name in names:
        import_, *attrs = name.split(":")
        assert len(attrs)
        mod = importlib.import_module(import_)
        operator.attrgetter(".".join(attrs))(mod).make()


def build_slugs(*names, base=_build):
    """
    Overload the :func:`!run()` method of a distutils build class to
    additionally call :func:`cslug.building.make`.

    :param names: Names to be passed to :func:`cslug.building.make`.
    :param base: An alternative base class to inherit from.
    :return: A modified subclass of **base**.

    """

    class build(base):

        def run(self):
            make(*names)
            super().run()

    return build


try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel
except ImportError:
    bdist_wheel = None
else:

    class bdist_wheel(_bdist_wheel):
        """:mod:`wheel.bdist_wheel` with platform dependent but Python
        independent tags.
        """
        def get_tag(self):
            python, abi, plat = _bdist_wheel.get_tag(self)
            # cslug packages contain binaries but they don't use
            # `#include <Python.h>` like traditional Python extensions.
            # This makes wheels dependent OS but not Python version dependent.
            from distutils.util import get_platform
            return python, abi, get_platform().replace("-", "_")


def copy_requirements(path="pyproject.toml",
                      ignore=("toml", "setuptools", "wheel")):
    """
    Parse the `build-system: requires` list from a :pep:`PEP518 pyproject.toml
    <0518#build-system-table>`.

    :param path: Specify an alternative toml file to parse from, defaults to
                 ``'pyproject.toml'``.
    :type path: Union[str, os.PathLike, io.TextIOBase]
    :param ignore: Requirements to ignore, use to remove build only
                   requirements, defaults to ``('toml', 'setuptools', 'wheel')``.
    :type ignore: Iterable[str]
    :return:
    :rtype: list[str]

    .. note::

        This function requires toml_. To use, you must mark ``'toml'`` as
        a build dependency, or if you use the ``--no-build-isolation`` option
        with pip, have toml_ installed.

    """

    import re
    import toml

    from cslug.misc import read, flatten
    ignore = flatten(ignore)

    conf = toml.loads(read(path)[0])
    requirements = conf["build-system"]["requires"]

    sep_re = re.compile(r"[<>=|&!\s]")
    return [i for i in requirements if sep_re.split(i)[0] not in ignore]
