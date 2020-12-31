import ctypes
from cslug import CSlug
class slug(CSlug):
    class dll(ctypes.CDLL):
        f = ctypes.CFUNCTYPE(ctypes.c_int)
        g = ctypes.CFUNCTYPE(ctypes.c_float)
