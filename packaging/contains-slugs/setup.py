# -*- coding: utf-8 -*-
"""
"""

from setuptools import setup, find_packages
from cslug.building import (build_slugs, bdist_wheel, CSLUG_SUFFIX,
                            copy_requirements)

setup(
    name="contains_slugs",
    version="1.0.0",
    author="Mr Slug",
    author_email="sluggy989@seaslugmail.com",
    url="www.toomanyslugs.com",
    packages=find_packages(),
    include_package_data=False,
    install_requires=copy_requirements(),
    package_data={
        "contains_slugs": ["*" + CSLUG_SUFFIX, "*.json"],
    },
    cmdclass={
        "build": build_slugs("contains_slugs:slug"),
        "bdist_wheel": bdist_wheel,
    },
)
