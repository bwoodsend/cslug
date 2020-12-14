# -*- coding: utf-8 -*-
"""
"""

import os
import shutil
from pathlib import Path
import re
from subprocess import run, PIPE

from cslug import exceptions


def which(name):
    if not os.path.dirname(name):
        return shutil.which(name)
    path = Path(name)

    if path.is_file():
        return name

    return shutil.which(path.name, path=str(path.parent))


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
    from textwrap import indent
    cmd = [cc(_cc), "-v"]
    p = run(cmd, stdout=PIPE, stderr=PIPE)
    stdout = p.stdout + p.stderr
    m = re.search(rb"(\S+) version (\S+)", stdout) \
        or re.search(rb"(pcc) (\S+) for \S+", stdout)
    try:
        name, version = m.groups()
        return name.decode(), tuple(map(int, version.split(b".")))
    except:  # pragma: no cover
        raise RuntimeError(
            f"Failed to get CC version from the output of\n    {cmd}\n::\n"
            f"{indent(stdout.decode(errors='replace'), '    ')}") from None
