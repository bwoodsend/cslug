# -*- coding: utf-8 -*-
"""
"""

import os, sys
from pathlib import Path
import random

import pytest

import cslug


def random_dir():
    """
    Pick a random existing folder that we have sufficient permission to access.

    """
    path = Path("/").resolve()
    for i in range(10):
        for _path in path.glob("*"):
            if _path.is_dir() and random.random() < .3:
                try:
                    os.listdir(_path)
                    path = _path
                except PermissionError:
                    continue

    return path


random_dirs = [random_dir() for i in range(3)]


@pytest.mark.parametrize("test_dir", random_dirs)
def test_unanchored(test_dir):
    _test_anchor(test_dir, test_dir, {})
    _test_anchor(test_dir, test_dir, {"__file__": "<string>"})


THIS_FILE = Path(__file__).resolve()


@pytest.mark.parametrize("test_dir", random_dirs)
def test_anchored(test_dir):
    _test_anchor(test_dir, THIS_FILE.parent, {"__file__": str(THIS_FILE)})


def _test_anchor(test_dir, prefix, namespace):
    old_wd = Path.cwd()
    target = [prefix, prefix / "hello", prefix / "foo" / "bar"]

    try:
        os.chdir(test_dir)

        namespace["cslug"] = cslug
        exec("paths = cslug.anchor('.', 'hello', 'foo/bar')", namespace)
        assert namespace["paths"] == target

    finally:
        os.chdir(old_wd)
