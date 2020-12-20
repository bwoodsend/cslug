# -*- coding: utf-8 -*-
"""
"""

import io

import pytest

from cslug import CSlug

from cslug._cc import cc_version

pytestmark = pytest.mark.order(-2)

from tests import name, RESOURCES, DUMP

SOURCE = RESOURCES / "unicode.c"


def delayed_skip_if_unsupported():
    """Skip unicode tests if the compiler is knonw not to support them.

    This is intentionally not a ``pytest.mark.skipif()`` to avoid evaluating
    this on test collection.
    """
    cc, version = cc_version()

    if cc == "gcc" and version < (10, 0, 0):
        pytest.skip("Unicode identifiers requires gcc 10.")
    if cc in ("tcc", "pcc"):
        pytest.skip("tcc doesn't support unicode.")


@pytest.mark.parametrize(
    "source", [SOURCE, io.StringIO(SOURCE.read_text("utf-8"))])
def test_from_file(source):
    delayed_skip_if_unsupported()

    slug = CSlug(DUMP / ("㟐㟐㟐" + name().name), source)
    slug._make_()
    assert slug._dll_.㟐(5) == 4
