# -*- coding: utf-8 -*-
"""
"""

import os, sys
from pathlib import Path
import io
import re

import pip

try:
    old = sys.stdout
    sys.stdout = file = io.StringIO()
    pip.__main__._main(["show", "cslug"])
finally:
    sys.stdout = old

dependents = re.search("Required-by:(.*)", file.getvalue()).group(1).strip().split()

