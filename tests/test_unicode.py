# -*- coding: utf-8 -*-
"""
"""

import io
import shutil
import platform

import pytest

from cslug import CSlug, anchor
from cslug._cc import cc_version

pytestmark = pytest.mark.order(-2)

from tests import name, RESOURCES, DUMP

# Unicode source files live in their own `unicode` folder.
UNICODE = RESOURCES / "unicode"


def delayed_skip_if_unsupported(feature, **compiler_versions):
    """Skip unicode tests if the compiler is known not to support them.

    This is intentionally not a ``pytest.mark.skipif()`` to avoid evaluating
    cc_version() on test collection.

    """
    cc, version = cc_version()

    supported_version = compiler_versions.get(cc, True)
    if supported_version is True:
        return
    if supported_version is False:
        pytest.skip(f"{feature} is not supported by {cc}.")
    if version < supported_version:
        pytest.skip(f"{feature} requires {cc} >= {supported_version}.")


no_windows = pytest.mark.skipif(
    platform.system() == "Windows",
    reason="No compilers recognise unicode filenames on Windows.")


@no_windows
def test_unicode_dll_path():
    """Test the filename to a DLL may contain unicode."""
    self = CSlug(DUMP / ("㟐㟐㟐" + name().name), RESOURCES / "basic.c")
    self.make()
    assert self.dll.add_1(-3) == -2


@no_windows
def test_unicode_source_path():
    """Test the filename to a .c source file may contain unicode."""
    unicode_filename = DUMP / ("㟐㟐㟐" + name().stem + ".c")
    shutil.copy(RESOURCES / "basic.c", unicode_filename)

    self = CSlug(unicode_filename)
    assert self.sources[0].exists()
    self.make()
    assert self.dll.add_1(-3) == -2


def _path_or_piped(path):
    return pytest.mark.parametrize(
        "source", [path, io.StringIO(path.read_text("utf-8"))],
        ids=["file", "piped"])


@_path_or_piped(UNICODE / "escaped-literal.c")
def test_escaped_unicode_literal(source):
    """Test a C source file may contain string literals containing escaped
    unicode characters."""
    self = CSlug(anchor(name()), source)
    self.make()
    assert self.dll.a() == "㟐"


@_path_or_piped(UNICODE / "literal.c")
def test_non_escaped_unicode_literal(source):
    """Test a C source file may contain unicode characters in string literals.
    """
    delayed_skip_if_unsupported("Unicode literals", pgcc=False)
    self = CSlug(anchor(name()), source)
    self.make()
    assert self.dll.a() == "㟐"


@_path_or_piped(UNICODE / "identifiers.c")
def test_unicode_identifiers(source):
    """Test unicode function/variable names."""
    delayed_skip_if_unsupported("Unicode identifiers", gcc=(10,), tcc=False,
                                pcc=False, clang=(3, 3), pgcc=False)

    slug = CSlug(anchor(name()), source)
    slug.make()
    assert slug.dll.㟐(5) == 4
