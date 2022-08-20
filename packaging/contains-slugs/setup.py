from setuptools import setup, find_packages
from cslug.building import (bdist_wheel, CSLUG_SUFFIX,
                            copy_requirements)

setup(
    install_requires=copy_requirements(),
    package_data={
        "contains_slugs": ["*" + CSLUG_SUFFIX, "*.json"],
    },
)
