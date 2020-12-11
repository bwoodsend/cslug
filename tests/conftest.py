# -*- coding: utf-8 -*-
"""
"""


def pytest_report_header(config):
    """
    Add C compiler name/version/availability and the chosen executable suffix to
    pytest's report header.

    https://docs.pytest.org/en/2.0.3/example/simple.html#adding-info-to-test-report-header
    """
    try:
        from cslug._cslug import SUFFIX
        from cslug._cc import cc_version
        v = cc_version()
    except Exception as ex:
        v = repr(ex)
        SUFFIX = "???"
    return ["cc={} version: {}".format(*v), "SUFFIX: " + SUFFIX]
