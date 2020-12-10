# -*- coding: utf-8 -*-
"""
"""


def pytest_report_header(config):
    """
    Add gcc version/availability and the chosen executable suffix to pytest's
    report header.

    https://docs.pytest.org/en/2.0.3/example/simple.html#adding-info-to-test-report-header
    """
    try:
        from cslug._cslug import gcc_version, SUFFIX
        v = gcc_version()
    except Exception as ex:
        v = repr(ex)
        SUFFIX = "???"
    return ["gcc version: {}".format(v), "SUFFIX: " + SUFFIX]
