# -*- coding: utf-8 -*-
"""
"""

import io

from cslug import CSlug, anchor

import pytest

from tests import name

pytestmark = pytest.mark.order(-1)


class CalledMake(Exception):
    """
    Not really an exception - just a signal to signify make() has been called.
    """
    pass


class Nested:
    class NameSpace:
        slug = CSlug(anchor(name(), io.StringIO("")))

        def make():
            raise CalledMake


def test_make():
    if __name__ == "__main__":
        pytest.xfail("This test won't work if run from main.")

    from cslug.building import make

    assert not Nested.NameSpace.slug.path.exists()
    assert not Nested.NameSpace.slug.types_map.json_path.exists()

    make("tests.test_building:Nested.NameSpace.slug")

    assert Nested.NameSpace.slug.path.exists()
    assert Nested.NameSpace.slug.types_map.json_path.exists()

    with pytest.raises(CalledMake):
        make("tests.test_building:Nested.NameSpace")

    with pytest.raises(CalledMake):
        make("tests.test_building:Nested:NameSpace")


def _pyproject_toml(source):
    source = f"[build-system]\nrequires={source}\n"
    return io.StringIO(source)


def test_copy_requirements():
    from cslug.building import copy_requirements
    assert copy_requirements(_pyproject_toml(["miff",  "muffet", "moof"])) \
           == ["miff", "muffet", "moof"]

    assert copy_requirements(_pyproject_toml(["miff", "muffet", "moof"]),
                             "miff") == ["muffet", "moof"]

    assert copy_requirements(_pyproject_toml(["miff", "moof", "toml"])) \
                             == ["miff", "moof"]
