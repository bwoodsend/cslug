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
from subprocess import PIPE, Popen, CompletedProcess
import re
from pathlib import Path
import venv
import sys
import shutil
import zipfile
import tarfile

from cslug.building import CSLUG_SUFFIX
from cslug.misc import block_compile

HERE = Path(__file__, "..").resolve()
CSLUG_ROOT = (HERE / "..").resolve()

contains_slugs = HERE / "contains-slugs"

# --- subprocess/env management ---
# This whole test is ran via subprocess calls.


def run(*args, cwd="."):
    old = os.getcwd()
    try:
        os.chdir(cwd)
        # This can be replaced by subprocess.run() when Python3.6 is ditched.
        p = Popen(list(map(str, args)), stdout=PIPE, stderr=PIPE)
        p.wait()
        return CompletedProcess(p.args, p.returncode,
                                p.stdout.read(), p.stderr.read())
    finally:
        os.chdir(old)


class Env(object):

    def __init__(self, dir):
        self.dir = dir

        builder = venv.EnvBuilder(system_site_packages=False, with_pip=True,
                                  clear=True)
        self.context = builder.ensure_directories(self.dir)
        builder.create(self.dir)
        assert Path(self.context.env_exe).exists()
        self.pip("install", "-U", "pip", "setuptools")

    def python(self, *args, cwd="."):
        return run(self.context.env_exe, *args, cwd=cwd)

    def pip(self, *args, cwd="."):
        return self.python("-m", "pip", "--disable-pip-version-check", "-q",
                           *args, cwd=cwd)


def master_python(*args, cwd="."):
    return run(sys.executable, *args, cwd=cwd)


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
    assert any(i.name == "c-code.c" for i in contents)

    for path in contents:
        # Binaries and type jsons should be excluded.
        assert path.suffix not in (".dll", ".so", ".dylib", ".json")

        # Random junk red-herrings should have been ignored.
        assert "junk" not in path.name


def inspect_wheel(wheel):
    """Inspect the contents of a ``contains-slugs`` wheel."""
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


def test():
    # Create a virtual environment.
    target = Env(HERE / "venv-dir")

    # Sanity check that `contains-slugs` isn't accessible via cwd or PYTHONPATH.
    p = target.python("-m", "contains_slugs")
    assert p.returncode
    assert re.search(b"No module named contains_slugs", p.stderr), p.stderr

    # Build a wheel for cslug using the master environment. This will be needed
    # later.
    p = master_python("setup.py", "-q", "bdist_wheel", cwd=CSLUG_ROOT)
    assert not p.returncode, p.stderr.decode()

    # Put some rubbish files into `contains-slugs`. These should not get
    # collected by either sdist or wheel.
    add_junk()

    # Clean dist, then build an sdist for `contains-slugs` using the master
    # environment.
    shutil.rmtree(contains_slugs / "dist", ignore_errors=True)
    p = master_python("setup.py", "-q", "sdist", cwd=contains_slugs)
    assert not p.returncode, p.stdout.decode() + p.stderr.decode()
    # Locate it.
    sdist = next((contains_slugs / "dist").glob("*"))
    # It should contain all source code and no cslug generated/binary artifacts.
    inspect_sdist(sdist)

    # `pip install` the sdist into the virtual environment. pip will build from
    # the sdist in an isolated environment, pulling in build dependencies
    # (i.e. cslug) automatically. Use `--find-links` to tell it where to find
    # our `contains-slugs` sdist and our wheel for `cslug`.
    p = target.pip("install", "contains-slugs", "--find-links",
                   contains_slugs / "dist", "--find-links", CSLUG_ROOT / "dist")
    assert not p.returncode, p.stderr.decode()

    # Test the contains slugs installation. `contains_slugs.__main__` contains
    # its own validations of which files it should and shouldn't have.
    p = target.python("-m", "contains_slugs")
    assert not p.returncode, p.stderr.decode()

    # Uninstall `contains-slugs`.
    p = target.pip("uninstall", "--yes", "contains-slugs")
    assert not p.returncode, p.stderr.decode()

    # bdist_wheel appears to lazily just copy `build/lib` which it really
    # shouldn't. If you `setup.py build` with two platforms which share a file
    # system then the second wheel will collect junk from the first. The only
    # way to stop it is to nuke your `build` folder. Even `setup.py clean` is
    # inadequate.
    shutil.rmtree(contains_slugs / "build", ignore_errors=True)

    # Build a wheel for `contains-slugs` using the master environment.
    shutil.rmtree(contains_slugs / "dist", ignore_errors=True)
    p = master_python("setup.py", "bdist_wheel", cwd=contains_slugs)
    assert not p.returncode, p.stderr.decode()
    # Again, locate and test its contents.
    wheel = next((contains_slugs / "dist").glob("*"))
    inspect_wheel(wheel)

    # Install the `contains-slugs` wheel whilst blocking `gcc`. The end user
    # should not need a C compiler to install a wheel.
    # Using `--find-links folder` instead of passing the `wheel` filename
    # directly verifies the platform tags (wheel's filename suffix) work.
    with block_compile():
        p = target.pip("install", "contains-slugs", "--find-links",
                       contains_slugs / "dist")
        assert not p.returncode, p.stderr.decode()

    # Test installation again.
    p = target.python("-m", "contains_slugs")
    assert not p.returncode, p.stderr.decode()


if __name__ == '__main__':
    test()
