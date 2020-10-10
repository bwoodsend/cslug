# -*- coding: utf-8 -*-
"""
"""


def make(*names):
    import importlib
    import operator

    for name in names:
        import_, *attrs = name.split(":")
        assert len(attrs)
        operator.attrgetter(*attrs)(importlib.import_module(import_)).make()
