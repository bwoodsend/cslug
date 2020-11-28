import numpy as np
from cslug import CSlug, anchor, ptr

slug = CSlug(anchor("deque.c"))
slug.make()


class Deque(object):

    def __init__(self, max_size, dtype):
        self.dtype = np.dtype(dtype)
        self.max_size = max_size
        self._contents = np.empty(max_size, self.dtype)

        self._raw = slug.dll.Deque(ptr(self._contents), self.max_size,
                                   self.dtype.itemsize, 0, self.max_size - 1)


if __name__ == "__main__":
    self = Deque(10, np.int)
    item = np.asarray(12)
    assert slug.dll.prepend(self._raw._ptr, ptr(item)) == 9
    assert self._contents[9] == 12
