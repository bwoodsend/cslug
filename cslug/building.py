# -*- coding: utf-8 -*-
"""
"""


def make(*names):
    import importlib
    import operator

    for name in names:
        import_, *attrs = name.split(":")
        assert len(attrs)
        mod = importlib.import_module(import_)
        operator.attrgetter(".".join(attrs))(mod).make()
