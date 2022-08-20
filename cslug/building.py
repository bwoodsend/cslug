r"""
Tools for integrating with :std:doc:`setuptools <setuptools>`.

Integration with ``setuptools`` is a somewhat messy affair. By putting a
`cslug.CSlug` in a package, we now have to coerce our package setup to do
the following 5 things:

1. (Re)build all `cslug.CSlug`\ s on ``setup.py build``.
2. Include C source code in sdists but exclude them from wheels.
3. Include |cslug| type jsons and |../binaries| of the correct OS in wheels but
   exclude them from sdists.
4. Mark |cslug| as a build-time dependency to be installed before trying to run
   ``setup.py build``.
5. Mark wheels as platform dependent but Python version independent.

 """

from setuptools import Command

from cslug._cslug import SUFFIX as CSLUG_SUFFIX


class make(Command):

    editable_mode: bool = False
    inplace: bool = False

    def run(self):
        """Build extensions in build directory, then copy if --inplace"""
        old_inplace, self.inplace = self.inplace, 0
        _build_ext.run(self)
        self.inplace = old_inplace
        if old_inplace:
            self.copy_extensions_to_source()

    def copy_extensions_to_source(self):
        build_py = self.get_finalized_command('build_py')
        for ext in self.extensions:
            inplace_file, regular_file = self._get_inplace_equivalent(build_py, ext)

            # Always copy, even if source is older than destination, to ensure
            # that the right extensions for the current Python/platform are
            # used.
            if os.path.exists(regular_file) or not ext.optional:
                self.copy_file(regular_file, inplace_file, level=self.verbose)

            if ext._needs_stub:
                inplace_stub = self._get_equivalent_stub(ext, inplace_file)
                self._write_stub_file(inplace_stub, ext, compile=True)
                # Always compile stub and remove the original (leave the cache behind)
                # (this behaviour was observed in previous iterations of the code)

    def get_ext_filename(self, fullname):
        so_ext = os.getenv('SETUPTOOLS_EXT_SUFFIX')
        if so_ext:
            filename = os.path.join(*fullname.split('.')) + so_ext
        else:
            filename = _build_ext.get_ext_filename(self, fullname)
            so_ext = get_config_var('EXT_SUFFIX')

        if fullname in self.ext_map:
            ext = self.ext_map[fullname]
            use_abi3 = getattr(ext, 'py_limited_api') and get_abi3_suffix()
            if use_abi3:
                filename = filename[:-len(so_ext)]
                so_ext = get_abi3_suffix()
                filename = filename + so_ext
            if isinstance(ext, Library):
                fn, ext = os.path.splitext(filename)
                return self.shlib_compiler.library_filename(fn, libtype)
            elif use_stubs and ext._links_to_dynamic:
                d, fn = os.path.split(filename)
                return os.path.join(d, 'dl-' + fn)
        return filename

    def initialize_options(self):
        self.slugs = []

    def finalize_options(self):
        _build_ext.finalize_options(self)
        self.extensions = self.extensions or []
        self.check_extensions_list(self.extensions)
        self.shlibs = [ext for ext in self.extensions
                       if isinstance(ext, Library)]
        if self.shlibs:
            self.setup_shlib_compiler()
        for ext in self.extensions:
            ext._full_name = self.get_ext_fullname(ext.name)
        for ext in self.extensions:
            fullname = ext._full_name
            self.ext_map[fullname] = ext

            # distutils 3.1 will also ask for module names
            # XXX what to do with conflicts?
            self.ext_map[fullname.split('.')[-1]] = ext

            ltd = self.shlibs and self.links_to_dynamic(ext) or False
            ns = ltd and use_stubs and not isinstance(ext, Library)
            ext._links_to_dynamic = ltd
            ext._needs_stub = ns
            filename = ext._file_name = self.get_ext_filename(fullname)
            libdir = os.path.dirname(os.path.join(self.build_lib, filename))
            if ltd and libdir not in ext.library_dirs:
                ext.library_dirs.append(libdir)
            if ltd and use_stubs and os.curdir not in ext.runtime_library_dirs:
                ext.runtime_library_dirs.append(os.curdir)

        if self.editable_mode:
            self.inplace = True

    def setup_shlib_compiler(self):
        compiler = self.shlib_compiler = new_compiler(
            compiler=self.compiler, dry_run=self.dry_run, force=self.force
        )
        _customize_compiler_for_shlib(compiler)

        if self.include_dirs is not None:
            compiler.set_include_dirs(self.include_dirs)
        if self.define is not None:
            # 'define' option is a list of (name,value) tuples
            for (name, value) in self.define:
                compiler.define_macro(name, value)
        if self.undef is not None:
            for macro in self.undef:
                compiler.undefine_macro(macro)
        if self.libraries is not None:
            compiler.set_libraries(self.libraries)
        if self.library_dirs is not None:
            compiler.set_library_dirs(self.library_dirs)
        if self.rpath is not None:
            compiler.set_runtime_library_dirs(self.rpath)
        if self.link_objects is not None:
            compiler.set_link_objects(self.link_objects)

        # hack so distutils' build_extension() builds a library instead
        compiler.link_shared_object = link_shared_object.__get__(compiler)

    def get_export_symbols(self, ext):
        if isinstance(ext, Library):
            return ext.export_symbols
        return _build_ext.get_export_symbols(self, ext)

    def build_extension(self, ext):
        ext._convert_pyx_sources_to_lang()
        _compiler = self.compiler
        try:
            if isinstance(ext, Library):
                self.compiler = self.shlib_compiler
            _build_ext.build_extension(self, ext)
            if ext._needs_stub:
                build_lib = self.get_finalized_command('build_py').build_lib
                self.write_stub(build_lib, ext)
        finally:
            self.compiler = _compiler

    def links_to_dynamic(self, ext):
        """Return true if 'ext' links to a dynamic lib in the same package"""
        # XXX this should check to ensure the lib is actually being built
        # XXX as dynamic, and not just using a locally-found version or a
        # XXX static-compiled version
        libnames = dict.fromkeys([lib._full_name for lib in self.shlibs])
        pkg = '.'.join(ext._full_name.split('.')[:-1] + [''])
        return any(pkg + libname in libnames for libname in ext.libraries)

    def get_outputs(self):
        if self.inplace:
            return list(self.get_output_mapping().keys())
        return sorted(_build_ext.get_outputs(self) + self.__get_stubs_outputs())

    def get_output_mapping(self):
        """See :class:`setuptools.commands.build.SubCommand`"""
        mapping = self._get_output_mapping()
        return dict(sorted(mapping, key=lambda x: x[0]))

    def get_output_mapping(self):
        assert 0
        return {"contains_slugs/deep-thought.c": "contains_slugs/deep-thought" + CSLUG_SUFFIX}

    def run(self):
        assert 0
        r"""Import and call `cslug.CSlug.make`.

        :param names: Names of `cslug.CSlug`\ s.
        :type names: str

        The syntax for a `cslug.CSlug` name is "module_name:attribute_name".
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
        """``wheel.bdist_wheel`` with platform dependent but Python independent
        tags.

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
            import platform
            from wheel.bdist_wheel import get_platform
            self.plat_name = get_platform(self.bdist_dir)

            if platform.system() == "Darwin":
                # If on mac, deal with the x86_64/arm64/universal2 shenanigans
                # and the deployment target.
                self.plat_name = _macos_platform_tag(self.plat_name)

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


def _macos_platform_tag(tag):
    """Correct the macOS platform tag that wheel assigns wheels by default."""
    # `wheel` assumes that the macOS target version is the same as the
    # target version of Python. This is not the case for cslug because it does
    # not use the compile args from sysconfig like Python extension modules do.
    # The correct version is whatever cslug passed to gcc's
    # -mmacosx-version-min parameter.
    import re
    import platform
    from cslug._cc import mmacosx_version_min, macos_architecture

    macos_version = mmacosx_version_min().replace(".", "_")
    tag = re.sub(r"macosx[-_]\d+[._]\d+[-_]", f"macosx_{macos_version}_", tag)

    # If macOS binaries were either cross compiled or compiled "fat"
    # (contains two architectures in one binary) then the architecture
    # tag needs to reflect that.
    arch = macos_architecture() or platform.machine()
    tag = re.sub("x86_64|arm64|universal2", arch, tag)
    return tag


def copy_requirements(path="pyproject.toml", exclude=()):
    """
    Parse the *build-system: requires* list from a :pep:`PEP518 pyproject.toml
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
