from pathlib import Path

from stdlib.parse import functions, Function


def cdef(f: Function):
    if f.index:
        out = f".. _`stdlib-{f.name}`:\n\n"
    else:
        out = ""
    platforms = ""
    for platform in availabilities:
        if f.name in availabilities[platform]:
            platforms += f"|{platform}| "
        else:
            platforms += "|blank| "
    return out + f"| :c:`{f.prototype}`\n" \
                 f"|    {platforms}\n" \
                 f"|    {f.description.replace('*', '**')}\n\n"


def cdef_library(name, contents):
    lines = [f"----\n\n{name}\n"]
    lines += [len(lines[0]) * "-" + "\n\n"]
    lines += [f"Functions defined with :c:`#include <{name}>`.\n\n"]
    lines += [cdef(i) for i in contents]
    return lines


lines = [
    """\
.. This file is computer-generated. Edit stdlib/docs.py instead of this file.

=============================
Access the C Standard Library
=============================

.. automodule:: cslug.stdlib

-------

The functions on this page are grouped by the header file they are included
from. Each function has a row of icons corresponding to the platforms that it
can be found on. See the key below for which platform each icon symbolises:

* |Android| Android
* |Cygwin| Cygwin (UNIX emulator for Windows).
* |FreeBSD| FreeBSD
* |glibc Linux| Linux distributions using GNU libc (i.e. the vast majority of them)
* |macOS| macOS (``x86_64`` or ``arm64``)
* |MSYS2| MSYS2 (another UNIX emulator for Windows)
* |musl Linux| Linux distributions using musl libc (most famously Alpine)
* |NetBSD| NetBSD
* |OpenBSD| OpenBSD
* |Windows MSVCRT| Windows 7 to 10 (using the MSVC runtime)
* |Windows UCRT| Windows 11 (using the new Universal C Runtime)

**Credits**: The textual descriptions on this page were taken from `here
<https://www.ibm.com/support/knowledgecenter/ssw_ibm_i_74/rtref/stalib.htm>`_.

"""
]

icons = list(Path(__file__, "../../docs/source/platforms").resolve().iterdir())
for file in icons:
    escaped = file.name.replace(" ", "\\ ")
    lines.extend((f".. |{file.stem}| image:: platforms/{escaped}\n"
                  f"    :height: 20px\n    :alt: {file.stem}\n\n",))
blank = next(
    icons.pop(i) for (i, path) in enumerate(icons) if path.stem == "blank")

availabilities = {}
for icon in icons:
    path = Path(__file__).with_name(icon.stem)
    if path.exists():
        availabilities[path.name] = set(
            path.read_text().strip("\n").splitlines())
    else:
        availabilities[path.name] = set()

lines = sum([cdef_library(i, functions[i]) for i in sorted(functions)], lines)

epilog = "".join(lines)
