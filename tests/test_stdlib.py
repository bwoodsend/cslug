# -*- coding: utf-8 -*-
"""
"""

import pytest

from cslug import stdlib, _stdlib

pytestmark = pytest.mark.order(-1)


def test_all_symbols_available():
    stdlib._std_types._merge_apply(_stdlib.stdlib, *_stdlib.extra_libs,
                                   strict=True)

    for name in stdlib._std_types.functions:
        assert hasattr(stdlib, name)
