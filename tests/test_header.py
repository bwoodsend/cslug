# -*- coding: utf-8 -*-
"""
"""

import enum
import io
import re

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


def test():
    self = Header(HERE / "dump" / "header.h", RESOURCES / "to_headerise.c",
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
    assert written == (RESOURCES / "target_header.h").read_text()
