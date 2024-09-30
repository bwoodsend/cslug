import os
import ctypes
import collections
import subprocess
import functools
from pprint import pprint

import requests
from progressbar import progressbar

from stdlib.parse import unavailable


@functools.lru_cache()
def is_universal(name):
    name = name.replace(".", "_") + ".html"
    # return requests.head("http://www.nirsoft.net/dll_information/windows8/" + name).ok
    # return requests.head("http://www.win7dll.info/" + name).ok
    return requests.head("http://xpdll.nirsoft.net/" + name).ok


# unavailable += [Function("printf", "", "", 0), Function("sqrt", "", "", 0)]

dlls = collections.defaultdict(list)

for path in progressbar(subprocess.getoutput("where *.dll").split("\n")):
    dirname, name = os.path.split(path)
    if "mingw" in dirname or "LLVM" in dirname:
        continue
    try:
        dll = ctypes.CDLL(path)
    except OSError:
        continue
    for func in unavailable:
        if hasattr(dll, func.name):
            if is_universal(name):
                dlls[name].append(func.name)

pprint(dict(dlls))

if __name__ == "__main__":
    pass
