import os
import time
import ctypes

import pytest

from cslug import stdlib

pytestmark = pytest.mark.order(-1)


def test_smoke():
    assert stdlib.log10(100) == 2

    if "USER" in os.environ:
        stdlib.getenv(b"USER").decode() == os.environ["USER"]
    else:
        assert stdlib.getenv(b"USER") is None

    assert stdlib.wcsncmp("hello", "héllo", 5) < 0
    assert stdlib.wcsncmp("héllo", "héllo", 5) == 0

    if os.name != "nt":
        stamp = 1656185193
        time_ptr = stdlib.localtime(ctypes.byref(ctypes.c_size_t(stamp)))
        assert stdlib.asctime(time_ptr) == (time.ctime(stamp) + "\n").encode()
