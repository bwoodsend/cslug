# -*- coding: utf-8 -*-
"""
End to end test for setuptools distributing a package containing CSlugs.

This ugly script simulates distributing a package that includes binaries
compiled via cslug, namely the `contains-slugs` dummy package sitting in this
directory.

The `contains-slugs` package is built to sdist and wheel. A virtual environment
without cslug (or anything else) is expected to install both formats without
complaint. The sdist should understand that it needs to install cslug before
looking at contains-slugs's setup.py. The wheel should be installable with gcc
hidden from `PATH`.

The sdist should strictly only contain C source files and no cslug artifacts.
The wheel on the other hand should only contain the cslug artifacts and no C
source code.

"""

import os

import re
from pathlib import Path
import textwrap
import venv
import sys
import shutil
import zipfile
import tarfile
import warnings

import pytest

from cslug.building import CSLUG_SUFFIX
from cslug.misc import block_compile

HERE = Path(__file__, "..").resolve()
CSLUG_ROOT = (HERE / "..").resolve()

contains_slugs = HERE / "contains-slugs"

# --- subprocess/env management ---
# This whole test is ran via subprocess calls.


def run(*args, cwd=".", check=True):
    from subprocess import PIPE, run
    env = os.environ.copy()
    env.update(PIP_DISABLE_PIP_VERSION_CHECK="1")
    old = os.getcwd()
    try:
        os.chdir(cwd)
        print("$", *args)
        p = run(list(map(str, args)), stdout=PIPE, stderr=PIPE, env=env)
        print(textwrap.indent((p.stdout + p.stderr).decode(), "    "))
    finally:
        os.chdir(old)
    if check:
        # Raise any errors.
        assert not p.returncode, p.stdout.decode() + p.stderr.decode()
        # Propagate any warnings.
        for line in p.stderr.decode().split("\n"):
            if re.search(r"\S", line):
                # These warnings are harmless and I can't find any way to
                # silence them.
                if re.search(
                        "no previously-included files matching .* found "
                        "under directory .*", line):
                    continue
                if re.search(r"no files found matching .* under directory .*",
                             line):
                    continue
                if re.search(r"does not exist.*can't clean it", line):
                    continue
                warnings.warn(line)
    return p


class Env(object):
    def __init__(self, dir):
        self.dir = dir

        builder = venv.EnvBuilder(system_site_packages=False, with_pip=True,
                                  clear=True)
        self.context = builder.ensure_directories(self.dir)
        builder.create(self.dir)
        assert Path(self.context.env_exe).exists()
        self.pip("install", "-U", "pip", "setuptools")

    def python(self, *args, cwd=".", check=True):
        return run(self.context.env_exe, *args, cwd=cwd, check=check)

    def pip(self, *args, cwd=".", check=True):
        return self.python("-m", "pip", "-q", "--no-cache-dir", *args, cwd=cwd,
                           check=check)


def master_python(*args, cwd=".", check=True):
    return run(sys.executable, *args, cwd=cwd, check=check)


# --- making a mess in the source code ---
# This junk should be ignored.


def add_junk():
    for path in ["junk.dll", "junk.so", "junk.dylib", "more-junk"]:
        (contains_slugs / "contains_slugs" / path).write_bytes(b"JUNK")


# --- Check contents of sdists/wheels ---


def inspect_sdist(sdist):
    """Inspect the contents of an ``contains-slugs`` sdist."""
    # Get a list of filenames contents.
    with tarfile.TarFile.open(sdist) as tf:
        contents = [Path(i) for i in tf.getnames()]

    # C code should be included.
    assert any(i.name == "deep-thought.c" for i in contents)

    for path in contents:
        # Binaries and type jsons should be excluded.
        assert path.suffix not in (".dll", ".so", ".dylib", ".json")

        # Random junk red-herrings should have been ignored.
        assert "junk" not in path.name


def inspect_wheel(wheel):
    """Inspect the contents of a ``contains-slugs`` wheel."""
    # Test `MACOS_DEPLOYMENT_TARGET` has been propagated into the filename.
    if "macos" in wheel.stem:
        from cslug._cc import mmacosx_version_min
        min_osx = mmacosx_version_min()
        # The '.' gets normalised to a '_'.
        assert re.search(min_osx.replace(".", r"\D"), wheel.stem)

    # Get a list of filenames contents.
    with zipfile.ZipFile(str(wheel), "r") as zf:
        contents = [Path(i) for i in zf.namelist()]

    # Binaries and type jsons should be included. `contains_slugs`, having one
    # CSlug, has exactly one of each.
    assert sum(path.name.endswith(CSLUG_SUFFIX) for path in contents) == 1
    assert sum(path.suffix == ".json" for path in contents) == 1

    for path in contents:
        # C source should be excluded.
        assert path.suffix not in (".c", ".h")

        # Random junk red-herrings should have been ignored.
        assert "junk" not in path.name

        # Binaries for other platforms should be automatically excluded.
        if path.suffix in (".dll", ".so", ".dylib"):
            assert path.name.endswith(CSLUG_SUFFIX)


# --- The test itself ---


@pytest.mark.order(-1)
@pytest.mark.timeout(300)
def test():
    if sys.platform == "cygwin":
        pytest.skip("venv is not supported on cygwin.")
        # TODO: virtualenv is technically (but flakely) supported but it lacks a
        #  programmatic API, requires some quite aggressive version pinning and
        #  is a pain to debug.

    # Create a virtual environment.
    target = Env(HERE / "venv-dir")

    # Sanity check that `contains-slugs` isn't accessible via cwd or PYTHONPATH.
    p = target.python("-m", "contains_slugs", check=False)
    assert p.returncode
    assert re.search(b"No module named contains_slugs", p.stderr), p.stderr

    # Clean out dist folder to prevent interference with wheels from previous
    # runs.
    if (CSLUG_ROOT / "dist").exists():
        [os.remove(i) for i in (CSLUG_ROOT / "dist").iterdir()]

    # Build a wheel for cslug using the master environment. This will be needed
    # later.
    p = master_python("setup.py", "-q", "bdist_wheel", cwd=CSLUG_ROOT)

    # Put some rubbish files into `contains-slugs`. These should not get
    # collected by either sdist or wheel.
    add_junk()

    # Clean dist, then build an sdist for `contains-slugs` using the master
    # environment.
    shutil.rmtree(contains_slugs / "dist", ignore_errors=True)
    p = master_python("setup.py", "-q", "sdist", cwd=contains_slugs)
    # Locate it.
    sdist = next((contains_slugs / "dist").glob("*"))
    # It should contain all source code and no cslug generated/binary artifacts.
    inspect_sdist(sdist)

    wheel_dump = contains_slugs / "wheels"
    wheel_dump.mkdir(exist_ok=True)
    p = target.pip("download", "setuptools", "wheel", "toml", cwd=wheel_dump)

    # `pip install` the sdist into the virtual environment. pip will build from
    # the sdist in an isolated environment, pulling in build dependencies
    # (i.e. cslug) automatically. Use `--find-links` to tell it where to find
    # our `contains-slugs` sdist, our wheel for `cslug` and wheels for
    # `setuptools`, `wheel` and `toml`. The `--no-index` blocks download from
    # PyPI. This is to force it to use this cslug version rather than to
    # download one from PyPI.
    p = target.pip("install", "contains-slugs", "--no-index", "--find-links",
                   contains_slugs / "dist", "--find-links", CSLUG_ROOT / "dist",
                   "--find-links", wheel_dump)

    # Test the contains slugs installation. `contains_slugs.__main__` contains
    # its own validations of which files it should and shouldn't have.
    p = target.python("-m", "contains_slugs")

    # Uninstall `contains-slugs`.
    p = target.pip("uninstall", "--yes", "contains-slugs")

    # bdist_wheel appears to lazily just copy `build/lib` which it really
    # shouldn't. If you `setup.py build` with two platforms which share a file
    # system then the second wheel will collect junk from the first.
    # `cslug.building.bdist_wheel.run()` should ensure that `clean` is called
    # automatically.
    # To verify that the cleaning is happening, inject some rubbish into the
    # build directory.
    for path in (contains_slugs / "build").rglob("*"):
        if path.is_dir():
            (path / "build-junk").write_text("I am full of rubbish")

    # Build a wheel for `contains-slugs` using the master environment.
    shutil.rmtree(contains_slugs / "dist", ignore_errors=True)
    p = master_python("setup.py", "-q", "bdist_wheel", cwd=contains_slugs)
    # Again, locate and test its contents.
    wheel = next((contains_slugs / "dist").glob("*"))
    inspect_wheel(wheel)

    # Install the `contains-slugs` wheel whilst blocking the compiler. The end
    # user should not need a C compiler to install a wheel.
    # Using `--find-links folder` instead of passing the `wheel` filename
    # directly verifies the platform tags (wheel's filename suffix) work.
    with block_compile():
        p = target.pip("install", "contains-slugs", "--find-links",
                       contains_slugs / "dist")

    # Test installation again.
    p = target.python("-m", "contains_slugs")


if __name__ == '__main__':
    test()
