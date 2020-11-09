# -*- coding: utf-8 -*-
"""
"""

from pathlib import Path

HERE = Path(__file__).parent
RESOURCES = HERE / "resources"

DUMP = HERE / "dump"
DUMP.mkdir(exist_ok=True)

def name():
    import uuid
    return Path("dump", str(uuid.uuid1()))
