import io
import platform
import contextlib

from cslug import CSlug, anchor

import pytest

from tests import name


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


@pytest.mark.parametrize("tag", [
    "macosx_10_9_x86_64",
    "macosx_11_3_x86_64",
    "macosx_12_0_arm64",
    "macosx_12_0_universal2",
])
def test_patch_macos_tag(monkeypatch, tag):
    from cslug.building import _macos_platform_tag

    with contextlib.suppress(KeyError):
        monkeypatch.delenv("MACOSX_ARCHITECTURE")

    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    with contextlib.suppress(KeyError):
        monkeypatch.delenv("MACOSX_ARCHITECTURE")
    with contextlib.suppress(KeyError):
        monkeypatch.delenv("MACOSX_DEPLOYMENT_TARGET")

    monkeypatch.setenv("MACOS_ARCHITECTURE", "x86_64")
    monkeypatch.setenv("MACOS_DEPLOYMENT_TARGET", "11")
    assert _macos_platform_tag(tag) == "macosx_11_0_x86_64"
    monkeypatch.delenv("MACOS_DEPLOYMENT_TARGET")
    assert _macos_platform_tag(tag) == "macosx_10_9_x86_64"

    monkeypatch.setenv("MACOS_ARCHITECTURE", "arm64")
    monkeypatch.setenv("MACOS_DEPLOYMENT_TARGET", "10.10")
    assert _macos_platform_tag(tag) == "macosx_11_0_arm64"
    monkeypatch.setenv("MACOS_DEPLOYMENT_TARGET", "12")
    assert _macos_platform_tag(tag) == "macosx_12_0_arm64"
    monkeypatch.setenv("MACOS_DEPLOYMENT_TARGET", "11.10")
    assert _macos_platform_tag(tag) == "macosx_11_10_arm64"
    monkeypatch.delenv("MACOS_DEPLOYMENT_TARGET")
    assert _macos_platform_tag(tag) == "macosx_11_0_arm64"

    monkeypatch.setenv("MACOS_ARCHITECTURE", "x86_64 arm64")
    monkeypatch.setenv("MACOS_DEPLOYMENT_TARGET", "12.7")
    assert _macos_platform_tag(tag) == "macosx_12_7_universal2"
    monkeypatch.delenv("MACOS_DEPLOYMENT_TARGET")
    assert _macos_platform_tag(tag) == "macosx_10_9_universal2"

    monkeypatch.setenv("MACOSX_ARCHITECTURE", "universal2")
    monkeypatch.setenv("MACOSX_DEPLOYMENT_TARGET", "12.7")
    assert _macos_platform_tag(tag) == "macosx_12_7_universal2"

    for key in ("MACOS_DEPLOYMENT_TARGET", "MACOSX_DEPLOYMENT_TARGET"):
        with contextlib.suppress(KeyError):
            monkeypatch.delenv(key)
    assert _macos_platform_tag(tag) == "macosx_10_9_universal2"

    for key in ("MACOS_ARCHITECTURE", "MACOSX_ARCHITECTURE"):
        with contextlib.suppress(KeyError):
            monkeypatch.delenv(key)
    assert "universal2" not in _macos_platform_tag(tag)
