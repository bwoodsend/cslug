import os, sys
from pathlib import Path
import runpy

import pytest

from cslug import CSlug
from tests import DEMOS, DOCS


def _test_demo(demo_path):
    old_cwd = os.getcwd()
    try:
        # The os.PathLike needs to be str() molly coddled when running with
        # coverage because there's a `filename.endswith()` somewhere in
        # coverage's code tracer.
        runpy.run_path(str(demo_path))
    finally:
        os.chdir(old_cwd)


def test_globals():
    _test_demo(DEMOS / "globals" / "globals.py")


def test_multi_output():
    _test_demo(DEMOS / "multi-output" / "multi-output.py")


def test_errors():
    _test_demo(DEMOS / "errors" / "errors.py")


string_count: CSlug = None


def test_string_count_make():
    slug = CSlug(DEMOS / "strings" / "strings-demo.c")
    slug.make()
    global string_count
    string_count = slug


@pytest.mark.parametrize("count", ["count", "count_"])
@pytest.mark.parametrize(("text", "char"), [("", "a"), ("hello", "l"),
                                            ("Мин печенье", "и")])
def test_count(count, text, char):
    if string_count is None:
        pytest.skip("Building strings-demo.c failed.")
    assert getattr(string_count.dll, count)(text, char) == text.count(char)


def test_str_reverse():
    _test_demo(DEMOS / "strings" / "reverse.py")


def test_arrays():
    _test_demo(DOCS / "source" / "arrays-and-buffers" / "arrays-demo.py")
    _test_demo(DOCS / "source" / "arrays-and-buffers" / "flatten.py")
