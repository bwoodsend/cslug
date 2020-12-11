# -*- coding: utf-8 -*-
"""
"""

import os
import shutil
from pathlib import Path
import re
from subprocess import Popen, PIPE, check_output
import platform

from cslug import exceptions

executable_suffixes = os.environ.get("pathext", "").split(os.pathsep)


def which(name):
    if not os.path.dirname(name):
        return shutil.which(name)
    path = Path(name)

    if path.is_file():
        return name

    for suffix in executable_suffixes:
        _path = path.with_suffix(suffix)
        if _path.is_file():
            return str(_path)


def cc(cc=None):
    cc = cc or os.environ.get("CC", "").strip()
    if cc == "block":
        raise exceptions.BuildBlockedError

    if cc:
        _cc = which(cc)
        if _cc is None:
            raise exceptions.CCNotFoundError(cc)
        return _cc

    cc = which("gcc")
    if cc is None:
        raise exceptions.NoGccError
    return cc


def cc_version(_cc=None):
    p = Popen([cc(_cc), "-v"], stdout=PIPE, stderr=PIPE,
              universal_newlines=True)
    p.wait()
    stdout = p.stdout.read() + p.stderr.read()
    name, version = re.search(r"(\S+) version (\S+)", stdout).groups()
    return name, tuple(map(int, version.split(".")))
