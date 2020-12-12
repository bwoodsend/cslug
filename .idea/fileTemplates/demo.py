import os

os.chdir(os.path.dirname(__file__))

import ctypes
from cslug import CSlug, ptr

slug = CSlug("${FILE_NAME}.c")
