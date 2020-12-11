# -*- coding: utf-8 -*-
"""
"""

import io

import pytest

from cslug import CSlug

from cslug._cc import cc_version

cc, version = cc_version()

pytestmark = [
    pytest.mark.skipif(cc == "gcc" and version < (10, 0, 0),
                       reason="Unicode identifiers requires gcc 10."),
    pytest.mark.order(-2),
]

from tests import name, RESOURCES, DUMP

SOURCE = RESOURCES / "unicode.c"


@pytest.mark.parametrize(
    "source", [SOURCE, io.StringIO(SOURCE.read_text("utf-8"))])
def test_from_file(source):
    slug = CSlug(DUMP / ("㟐㟐㟐" + name().name), source)
    slug.make()
    assert slug.dll.㟐(5) == 4
