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


def which(name):
    if not os.path.dirname(name):
        return shutil.which(name)
    path = Path(name)

    if path.is_file():
        return name

    for suffix in os.environ.get("pathext", "").split(os.pathsep):
        _path = path.with_suffix(suffix)
        if _path.is_file():
            return str(_path)
    raise FileNotFoundError(name)


def cc(cc=None):
    cc = cc or os.environ.get("CC", "").strip()
    if cc == "block":
        raise exceptions.BuildBlockedError

    if cc:
        _cc = which(cc)
        if _cc is None:
            raise exceptions.CCNotFoundError(cc)
        return _cc
    else:
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


activator = r"C:\links\mingw-activate.bat"

activator = "echo"


def _env_after_calling(command):
    if platform.system() == "Windows":
        command = f"{activator} && set"
        encoding = "oem"
    else:
        command = f"source {activator} && printenv"
        encoding = "utf-8"

    output = check_output(command, encoding=encoding, shell=True)
    return dict(re.findall(r"(\w+)=(.*)", output))


def cc_activate(activate=None):
    activate = activate or os.environ.get("cc_activate")
    if not activate:
        return
    return _env_after_calling(activate)
