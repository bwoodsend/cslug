# -*- coding: utf-8 -*-
"""
"""
import re
from pathlib import Path

jargon = Path(__file__, "..", "jargon.rst").read_text("utf-8")

item_head_re = r"""
\n
[ ]{4}(?![ ])(.+)\n
[ ]*\n
((?:[ ]{8}(?![ ]).+\n)*)
"""

item_head_re = re.compile(item_head_re, re.VERBOSE)  # yapf: disable

epilog = ""

for match in item_head_re.finditer(jargon):
    name = match.group(1)
    head = re.sub(r"\s+", " ", match.group(2)).strip()
    head = re.sub(r":[^:]*:`([^`]+)`", r"\1", head)
    head = re.sub(r"\|([^|]*)", r"\1", head)

    epilog += '.. |{}| replace:: :tooltip:`'.format(name)
    epilog += \
    '<a href="jargon.html#term-{}">{}<span class="tooltiptext">{}</span></a>'\
        .format(name.lower().replace(" ", "-"), name, head) + "`\n"

if __name__ == '__main__':
    print(epilog)
