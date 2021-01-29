# -*- coding: utf-8 -*-
"""
"""

import enum
import io
import re

import pytest

from cslug import Header

from tests import RESOURCES, HERE


class Farmers(enum.Enum):
    Boggis = enum.auto()
    Bunce = enum.auto()
    Bean = enum.auto()


class Burger(enum.IntFlag):
    BORING = 0
    IS_DOUBLE = enum.auto()
    HAS_TOMATO = enum.auto()
    HAS_BACON = enum.auto()


StatusCodes = {
    "OK": 0,
    "NOT_OK": 1,
    "DISASTER": 2,
}


@pytest.mark.parametrize("pseudo_input", [False, True])
def test(pseudo_input):
    source = RESOURCES / "to_headerise.c"
    if pseudo_input:
        source = io.StringIO(source.read_text())

    self = Header(HERE / "dump" / "a header-file.h", source,
                  defines=(Farmers, StatusCodes, Burger), includes="<stdio.h>")
    file = io.StringIO()
    self.write(file)
    written = file.getvalue()

    # --- Minimal linter checks ---
    # No trailing whitespace.
    assert not any(re.finditer("[ \t]$", written))
    # Single trailing `\n`.
    assert written.endswith("\n") and not written.endswith("\n\n")

    # Ae want automatically generated headers to be as git-friendly as possible
    # (although checking them into git is still not recommended) we aim for
    # exact byte-for-byte reproducibility.
    target = (RESOURCES / "target_header.h").read_text()
    if pseudo_input:
        target = target.replace("to_headerise.c", "<string>")
    assert written == target


def test_implicit_name_no_includes_sourceless():
    self = Header(RESOURCES / "non-existent.c")
    assert self.sources == [RESOURCES / "non-existent.c"]
    assert self.path == RESOURCES / "non-existent.h"
    assert not self.path.exists()


def test_include_local_or_system():
    from cslug._headers import _include_local_or_system
    assert _include_local_or_system('x') == '"x"'
    assert _include_local_or_system('"x"') == '"x"'
    assert _include_local_or_system('"x"""') == '"x"'
    assert _include_local_or_system('x"') == '"x"'
    assert _include_local_or_system('<x>') == '<x>'
