import re
from pathlib import Path

jargon = Path(__file__, "..", "jargon.rst").resolve().read_text("utf-8")


def uncapitalise(x):
    return " ".join(i if i.isupper() else i.lower() for i in x.split(" "))


def pluralise(x):
    if x[-1] == "s":
        return x + "es"
    if x[-1] == "y":
        return x[:-1] + "ies"
    return x + "s"


item_head_re = r"""
\n
[ ]{4}(?![ ])(.+)\n
[ ]*\n
((?:[ ]{8}(?![ ]).+\n)*)
"""

item_head_re = re.compile(item_head_re, re.VERBOSE)  # yapf: disable


def tooltip(title, body, path=""):
    # I hate string normalisation.
    text_name = uncapitalise(title)
    hyperlink = title.replace(" ", "-")
    rst_sub_name = title.lower()
    return _tooltip(rst_sub_name, text_name, hyperlink, body, path) + \
        _tooltip(pluralise(rst_sub_name), pluralise(text_name), hyperlink, body, path)


def _tooltip(rst_sub_name, text_name, hyperlink_title, body, path=""):
    return '.. |{}{}| replace:: :tooltip:`'.format(path, rst_sub_name) + \
            '<a href="{}jargon.html#term-{}">'.format(path, hyperlink_title) + \
            text_name + \
            '<span class="tooltiptext">{}</span></a>'.format(body) + \
            "`\n"


epilog = ""

for match in item_head_re.finditer(jargon):
    head = re.sub(r"\s+", " ", match.group(2)).strip()
    head = re.sub(r":[^:]*:`([^`]+)`", r"\1", head)
    head = re.sub(r"\|([^|]*)", r"\1", head)

    epilog += tooltip(match.group(1), head)
    # HACK: This raw href="jargon.html" is dependent of the position of the
    #       document which contains it. Any page in a subdirectory (namely the
    #       (API reference) gives broken links. As a miserable compromise, use
    #       |../substitution| in these pages to indicate use
    #       href="../jargon.html".
    epilog += tooltip(match.group(1), head, "../")

if __name__ == '__main__':
    print(epilog)
