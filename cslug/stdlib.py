# -*- coding: utf-8 -*-
"""
Standard library C functions exposed to Python.

"""


def _init():
    import io
    from pathlib import Path
    from cslug import __loader__, Types
    from cslug._stdlib import stdlib
    json = Path(__file__).with_suffix(".json")

    _std_types = Types(io.StringIO(__loader__.get_data(str(json)).decode()))
    _std_types.init_from_json()

    _std_types.apply(stdlib)
    __all__ = list(_std_types.types["functions"])
    for name in __all__:
        globals()[name] = getattr(stdlib, name)

    return _std_types, __all__


_std_types, __all__ = _init()
