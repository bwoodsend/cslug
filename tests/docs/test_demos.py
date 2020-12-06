# -*- coding: utf-8 -*-
"""
"""

import os, sys
from pathlib import Path
import runpy

import pytest

pytestmark = pytest.mark.order(-2)

from tests import DEMOS


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
