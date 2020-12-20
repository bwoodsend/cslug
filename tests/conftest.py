# -*- coding: utf-8 -*-
"""
"""
import pytest


def pytest_report_header(config):
    """
    Add C compiler name/version/availability and the chosen executable suffix to
    pytest's report header.

    https://docs.pytest.org/en/2.0.3/example/simple.html#adding-info-to-test-report-header
    """
    try:
        from cslug._cslug import SUFFIX
        from cslug._cc import cc_version, cc
        import os
        v = cc_version()

        # If using the `pcc` compiler, hackily monkey-patch the
        # `CSlug._compile_command_()` to skip any test using stdin-piped source
        # code. (Gross, I know.)
        if v[0] == "pcc":
            from cslug import CSlug
            old = CSlug._compile_command_

            def compile_command(self, _cc=None):
                cmd, buffers = old(self, _cc)
                if buffers:
                    pytest.xfail("pcc doesn't support piped sources.")
                return cmd, buffers

            CSlug._compile_command_ = compile_command

        return [
            f"env CC: '{os.environ.get('CC')}'", f"cc(): '{cc()}' ",
            f"cc_version(): {cc_version()}", "SUFFIX: " + SUFFIX
        ]
    except Exception as ex:
        return [f"Header failed with {ex}"]
