# -*- coding: utf-8 -*-
"""
"""

import io

from cslug import CSlug, anchor

import pytest

from tests import name

pytestmark = pytest.mark.order(-1)


class Nested:

    class NameSpace:
        slug = CSlug(anchor(name(), io.StringIO("")))


def test_make():
    from cslug.building import make

    assert not Nested.NameSpace.slug.path.exists()
    assert not Nested.NameSpace.slug.types_dict.json_path.exists()

    make("tests.test_building:Nested.NameSpace.slug")

    assert Nested.NameSpace.slug.path.exists()
    assert Nested.NameSpace.slug.types_dict.json_path.exists()
