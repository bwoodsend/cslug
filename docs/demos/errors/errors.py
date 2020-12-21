# yapf: disable
import os
os.chdir(os.path.dirname(__file__))

import enum
import ctypes
from cslug import CSlug, Header


class Status(enum.Enum):
    """Status codes to indicate different error types."""
    OK = enum.auto()
    LOG_OF_0_ERROR = enum.auto()
    LOG_OF_NEGATIVE_VALUE_ERROR = enum.auto()


slug = CSlug("pedantic-log.c", headers=Header("status-codes.h", defines=Status))


def log(x):
    """Fussy natural logarithm which raises exceptions for invalid inputs."""

    out = ctypes.c_double()
    status = Status(slug.dll.pedantic_log(x, ctypes.byref(out)))

    if status is not Status.OK:
        # If you're feeling especially motivated you could write a custom error
        # message for each outcome - I am not feeling such a motivation...
        error = status.name.replace("_", " ").lower()
        raise ValueError(f"log({x}) triggered a {error}.")

    return out.value


# --- Test code ---

import math
import pytest

with pytest.raises(ValueError): log(0)
with pytest.raises(ValueError): log(-2)
assert log(1) == 0
assert log(math.e) == pytest.approx(1)
assert log(math.e ** 12.3) == pytest.approx(12.3)
