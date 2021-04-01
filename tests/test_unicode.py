# -*- coding: utf-8 -*-
"""
"""

import io
import shutil

import pytest

from cslug import CSlug, anchor
from cslug._cc import cc_version

pytestmark = pytest.mark.order(-2)

from tests import name, RESOURCES, DUMP

# Unicode source files live in their own `unicode` folder.
UNICODE = RESOURCES / "unicode"


def delayed_skip_if_unsupported():
    """Skip unicode tests if the compiler is known not to support them.

    This is intentionally not a ``pytest.mark.skipif()`` to avoid evaluating
    this on test collection.
    """
    cc, version = cc_version()

    if cc == "gcc" and version < (10, 0, 0):
        pytest.skip("Unicode identifiers requires gcc 10.")
    if cc in ("tcc", "pcc"):
        pytest.skip("tcc doesn't support unicode.")
    if cc == "clang" and version < (3, 3, 0):
        pytest.skip("Unicode identifiers requires clang 3.3.")


def test_unicode_dll_path():
    """Test the filename to a DLL may contain unicode."""
    self = CSlug(DUMP / ("㟐㟐㟐" + name().name), RESOURCES / "basic.c")
    self.make()
    assert self.dll.add_1(-3) == -2


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
    assert self.dll.b() == "🚀"


@_path_or_piped(UNICODE / "literal.c")
def test_non_escaped_unicode_literal(source):
    """Test a C source file may contain unicode characters in string literals.
    """
    self = CSlug(anchor(name()), source)
    self.make()
    assert self.dll.a() == "㟐"
    assert self.dll.b() == "🚀"


@_path_or_piped(UNICODE / "identifiers.c")
def test_unicode_identifiers(source):
    """Test unicode function/variable names."""
    # Not many compilers support this.
    delayed_skip_if_unsupported()

    slug = CSlug(anchor(name()), source)
    slug.make()
    assert slug.dll.㟐(5) == 4
