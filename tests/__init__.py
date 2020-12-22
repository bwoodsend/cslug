# -*- coding: utf-8 -*-
"""
"""

from pathlib import Path
from uuid import uuid1 as uuid

HERE = Path(__file__).parent
RESOURCES = HERE / "resources"
DEMOS = HERE / ".." / "docs" / "demos"

DUMP = HERE / "dump"
DUMP.mkdir(exist_ok=True)

assert HERE.is_dir()
assert RESOURCES.is_dir()
assert DEMOS.is_dir()
assert DUMP.is_dir()


def name():
    return Path("dump", str(uuid()))


def filter_warnings(*args, **kwargs):
    import warnings

    def wrapper(test):
        def wrapped():
            with warnings.catch_warnings():
                warnings.filterwarnings(*args, **kwargs)
                return test()

        wrapped.__name__ = test.__name__
        return wrapped

    return wrapper
