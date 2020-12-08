# -*- coding: utf-8 -*-
"""
"""
import re
from pathlib import Path

jargon = Path(__file__, "..", "jargon.rst").read_text("utf-8")


def uncapitalise(x):
    return " ".join(i if i.isupper() else i.lower() for i in x.split(" "))


item_head_re = r"""
\n
[ ]{4}(?![ ])(.+)\n
[ ]*\n
((?:[ ]{8}(?![ ]).+\n)*)
"""

item_head_re = re.compile(item_head_re, re.VERBOSE)  # yapf: disable

epilog = ""

for match in item_head_re.finditer(jargon):
    head = re.sub(r"\s+", " ", match.group(2)).strip()
    head = re.sub(r":[^:]*:`([^`]+)`", r"\1", head)
    head = re.sub(r"\|([^|]*)", r"\1", head)

    # I hate string normalisation.
    heading_name = match.group(1)
    text_name = uncapitalise(heading_name)
    hyperlink_title = heading_name.replace(" ", "-")
    rst_sub_name = heading_name.lower()

    epilog += '.. |{}| replace:: :tooltip:`'.format(rst_sub_name)
    epilog += \
    '<a href="jargon.html#term-{}">{}<span class="tooltiptext">{}</span></a>'\
        .format(hyperlink_title, text_name, head) + "`\n"

if __name__ == '__main__':
    print(epilog)
