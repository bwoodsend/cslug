# -*- coding: utf-8 -*-
"""
"""

import os, sys
import platform
import re

import pytest

from cslug._cc import cc, cc_version, which
from cslug import exceptions, misc

from tests import DUMP, uuid

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
    # Windows needs is case folded. msys2 like to strip executable suffix.
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
        assert cc() == which("gcc")

        misc.hide_from_PATH("gcc")
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
