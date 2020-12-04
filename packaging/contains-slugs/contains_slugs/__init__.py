# -*- coding: utf-8 -*-
"""
"""

from cslug import CSlug, anchor

slug = CSlug(anchor("c-code.c"))


def test():
    assert slug.path.exists()
    assert slug.types_dict.json_path.exists()
    assert not slug.sources[0].exists()
    print("ok")
