# -*- coding: utf-8 -*-
"""
"""

from pathlib import Path
from uuid import uuid1 as uuid
from functools import wraps

HERE = Path(__file__).parent.resolve()
RESOURCES = HERE / "resources"
ROOT = HERE.parent
DOCS = ROOT / "docs"
DEMOS = DOCS / "demos"

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
        @wraps(test)
        def wrapped(*_test_args, **_test_kwargs):
            with warnings.catch_warnings():
                warnings.filterwarnings(*args, **kwargs)
                return test(*_test_args, **_test_kwargs)

        return wrapped

    return wrapper


warnings_are_evil = filter_warnings("error")
