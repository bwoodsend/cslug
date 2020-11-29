# -*- coding: utf-8 -*-
"""
"""

import os, sys
from pathlib import Path
import runpy

import pytest

pytestmark = pytest.mark.order(-2)

from tests import DEMOS


def test():
    old_cwd = os.getcwd()
    try:
        # The os.PathLike needs to be str() molly coddled when running with
        # coverage because there's a `filename.endswith()` somewhere in
        # coverage's code tracer.
        runpy.run_path(str(DEMOS / "globals" / "globals.py"))
    finally:
        os.chdir(old_cwd)
