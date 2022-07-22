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

        return [
            f"env CC: '{os.environ.get('CC')}'", f"cc(): '{cc()}' ",
            f"cc_version(): {cc_version()}", "SUFFIX: " + SUFFIX
        ]
    except Exception as ex:
        return [f"Header failed with {ex}"]
