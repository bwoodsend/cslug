# -*- coding: utf-8 -*-
r"""
Tools for integrating with :std:doc:`setuptools <setuptools>`.

Integration with ``setuptools`` is a somewhat messy affair. By putting a
:class:`cslug.CSlug` in a package, we now have to coerce our package setup to do
the following 5 things:

1. (Re)build all :class:`cslug.CSlug`\ s on ``setup.py build``.
2. Include C source code in sdists but exclude them from wheels.
3. Include |cslug| type jsons and |../binaries| of the correct OS in wheels but
   exclude them from sdists.
4. Mark |cslug| as a build-time dependency to be installed before trying to run
   ``setup.py build``.
5. Mark wheels as platform dependent but Python version independent.

 """

from distutils.command.build import build as _build
from cslug._cslug import SUFFIX as CSLUG_SUFFIX


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


# Trying to properly coverage trace these is too much hassle.


def build_slugs(*names, base=_build):  # pragma: no cover
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

except ImportError:  # pragma: no cover
    # Provide a self-explanatory error message on `setup.py bdist_wheel` if the
    # user doesn't have wheel installed.
    from distutils.cmd import Command

    class bdist_wheel(Command):
        user_options = []

        def finalize_options(self) -> None:
            pass

        def initialize_options(self) -> None:
            pass

        def run(self):
            raise SystemExit(
                "ERROR: The bdist_wheel command requires the wheel package. "
                "Please `pip install wheel` then try again.")
else:

    class bdist_wheel(_bdist_wheel):
        """:mod:`!wheel.bdist_wheel` with platform dependent but Python
        independent tags.

        In addition to setting the tags, also prevent setuptools's build cache
        from leaking binaries for the wrong platform into the wheel. See
        :meth:`run` for details.

        """
        def finalize_options(self):  # pragma: no cover
            """Set platform dependent wheel tag.

            |cslug| packages contain binaries but they don't use
            :c:`#include <Python.h>` like traditional Python extensions do.
            This makes wheels dependent OS but not Python version dependent.
            """
            # Tag setting is done by ``bdist_wheel.get_tag()`` later in the
            # build but overloading that means reimplementing some rather
            # complex platform normalisation. Injecting the platform name here,
            # before the normalisation, ensures that it gets normalised.
            # Setting ``plat_name`` is equivalent to using the ``--plat`` CLI
            # option.
            import re, os
            from wheel.bdist_wheel import get_platform
            self.plat_name = get_platform(self.bdist_dir)

            # `wheel` assumes that the macOS target version is the same as the
            # target version of Python. This is completely irrelevant to cslug.
            # The correct version is whatever cslug passed to gcc's
            # -mmacosx-version-min parameter.
            from cslug._cc import mmacosx_version_min, macos_architecture
            min_osx = mmacosx_version_min()
            self.plat_name = re.sub(r"macosx-\d+[.]\d+-", f"macosx-{min_osx}-",
                                    self.plat_name)
            # If macOS binaries were either cross compiled or compiled "fat"
            # (contains two architectures in one binary) then the architecture
            # tag needs to reflect that.
            arch = macos_architecture()
            if arch:
                self.plat_name = re.sub("x86_64|arm64", arch, self.plat_name)

            super().finalize_options()

        def run(self):  # pragma: no cover
            """Additionally run ``setup.py clean --all`` before building the
            wheel.

            Setuptools's caching can cause files for the wrong platform to be
            collected if you build wheels for the two platforms on the same
            filesystem. This can happen by switching from 64 to 32 bit
            Python, using Docker, dual booting or any kind of cross compiling.

            Forcing a clean will ensure that no files are included in wheels
            which they shouldn't be.

            .. versionchanged:: v0.4.0

                Add this force-cleaning step.

            """
            clean = self.distribution.get_command_obj("clean")
            clean.all = True
            clean.verbose = 0
            self.run_command("clean")
            super().run()


def copy_requirements(path="pyproject.toml", exclude=()):
    """
    Parse the `build-system: requires` list from a :pep:`PEP518 pyproject.toml
    <0518#build-system-table>`.

    :param path: Specify an alternative toml file to parse from, defaults to
                 ``'pyproject.toml'``.
    :type path: str or os.PathLike or io.TextIOBase
    :param exclude: Requirements to exclude, use to remove build only
                   requirements.
    :type exclude: Iterable[str]
    :return:
    :rtype: list[str]

    .. note::

        This function requires toml_. To use, you must mark ``'toml'`` as
        a build dependency, or if you use the ``--no-build-isolation`` option
        with pip, have toml_ installed.

    .. note::

        toml_ wheel and setuptools are always excluded. If you want to re-add
        them then append them after::

            copy_requirements() + ["toml"]

    """

    import re
    import toml

    from cslug.misc import read, flatten
    exclude = flatten(exclude) + ["wheel", "setuptools", "toml"]

    conf = toml.loads(read(path)[0])
    requirements = conf["build-system"]["requires"]

    sep_re = re.compile(r"[<>=|&!\s]")
    return [i for i in requirements if sep_re.split(i)[0] not in exclude]
