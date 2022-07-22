import os, sys
import platform
import re

import pytest

from cslug._cc import cc, which, _parse_cc_version, _macos_architecture
from cslug import exceptions, misc
from cslug._cslug import strip_useless_warnings

from tests import DUMP, uuid, RESOURCES

pytestmark = pytest.mark.order(-4)

if platform.system() == "Windows":
    executable_suffixes = os.environ["PATHEXT"].strip(";").split(";")
elif re.search("msys", platform.system(), re.IGNORECASE):
    executable_suffixes = [".exe"]
else:
    executable_suffixes = [""]


def eq(x, y):
    assert x is not None
    # Strictly no PathLikes here.
    assert isinstance(x, str)
    # Windows needs its case folded. msys2 like to strip the executable suffix.
    assert os.path.splitext(os.path.normcase(x))[0] \
           == os.path.splitext(os.path.normcase(str(y)))[0]


@pytest.mark.parametrize("suffix", executable_suffixes)
def test_which(suffix):
    DIR = DUMP / str(uuid())
    DIR.mkdir()
    path = (DIR / "sausage-cc").with_suffix(suffix)
    if path.exists():
        os.remove(path)

    # Full, non-existent path - raise an error.
    assert which(str(path)) is None
    with pytest.raises(
            exceptions.CCNotFoundError,
            match=f"compiler {re.escape(str(path))} .* "
            f"does not exist[.]"):
        cc(str(path))

    # Make `path` exist.
    path.write_bytes(b"#!/usr/bin/bash")
    path.chmod(0o755)

    # Full path which does exist - return that path.
    assert which(str(path)) == str(path)
    assert cc(str(path)) == str(path)
    # Stripping the suffix should still work.
    eq(which(str(path.with_suffix(""))), path)
    eq(cc(str(path.with_suffix(""))), path)

    # This file is not in PATH so shouldn't be findable by name only - raise
    # error saying to add to PATH.
    for name in [path.name, path.stem]:
        assert which(name) is None
        with pytest.raises(
                exceptions.CCNotFoundError,
                match=f"the compiler {re.escape(name)} .*"
                f"Try adding .* to PATH"):
            cc(name)

    # Add to PATH - should now be findable by name.
    old = os.environ["PATH"]
    try:
        os.environ["PATH"] += os.pathsep + str(DIR)
        print(os.environ["PATH"])
        import shutil
        assert shutil.which(path.name)

        eq(which(path.name), path)
        eq(which(path.stem), path)
        eq(cc(path.name), path)
        eq(cc(path.stem), path)

    finally:
        os.environ["PATH"] = old


def test_no_cc_or_blocked_error():

    old = os.environ.copy()
    try:
        os.environ.pop("CC", None)
        try:
            if platform.system() in ("Darwin", "FreeBSD", "OpenBSD"):
                assert cc() == (which("clang") or which("gcc"))
            else:
                assert cc() == which("gcc")
        except exceptions.NoGccError:
            pass

        misc.hide_from_PATH("gcc")
        misc.hide_from_PATH("clang")
        with pytest.raises(exceptions.NoGccError,
                           match=".* requires gcc .* in the PATH."):
            cc()
    finally:
        os.environ.clear()
        os.environ.update(old)

    with pytest.raises(exceptions.BuildBlockedError):
        with misc.block_compile():
            cc()
    str(exceptions.BuildBlockedError())

    assert cc()


cc_version_files = list((RESOURCES / "cc_versions").glob("*"))


@pytest.mark.parametrize("path", cc_version_files,
                         ids=[i.name for i in cc_version_files])
def test_cc_version_parse(path):
    """Test the parsing of ``$CC -v`` or ``$CC --version`` outputs.

    So that these can be easily tested on all platforms, sample outputs of
    ``$CC -v`` or ``$CC --version`` are dumped in files located at
    tests/resources/cc_versions.

    """
    # The intended parse output is the filename.
    name, version, _ = path.name.split("-")
    version = tuple(map(int, version.split(".")))

    # The file contents is the stdout that is dumped by the compiler.
    stdout = path.read_bytes()

    # Check the target matches what is parsed.
    parsed = _parse_cc_version(stdout, "")
    assert (name, version) == parsed


CC_VERSION_ERROR_MESSAGE = """\
Failed to .* output of
    \\['unknown-cc', '-v'\\]
::
    Miff muffet moof compiler with added miffle."""


def test_failed_cc_version():
    with pytest.raises(RuntimeError, match=CC_VERSION_ERROR_MESSAGE):
        _parse_cc_version(b"Miff muffet moof compiler with added miffle.",
                          ["unknown-cc", "-v"])


def test_macos_architecture():
    assert _macos_architecture("x86_64") == "x86_64"
    assert _macos_architecture("universal2") == "universal2"
    assert _macos_architecture("") is None
    assert _macos_architecture(None) is None
    assert _macos_architecture("x86_64, arm64") == "universal2"
    assert _macos_architecture("x86_64 arm64") == "universal2"
    assert _macos_architecture("x86_64,arm64") == "universal2"
    with pytest.raises(EnvironmentError, match="The MACOS_ARCHITECTURE .*"):
        _macos_architecture("spaghetti")


def test_strip_useless_warnings():
    assert strip_useless_warnings(
        '"/tmp/05fa2e86-3c3a-11ec-a499-586c251818cf.c", line 6: '
        'warning: last line of file ends without a newline\n     ^') == ""

    assert strip_useless_warnings(
        '/opt/nvidia/hpc_sdk/Linux_x86_64/21.9/compilers/lib/nvhpc.ld '
        'contains output sections; did you forget -T?') == ''
