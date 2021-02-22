# -*- coding: utf-8 -*-
"""
"""

from setuptools import setup, find_packages
import runpy

with open('README.rst') as readme_file:
    readme = readme_file.read()

setup(
    author="Brénainn Woodsend",
    author_email='bwoodsend@gmail.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    description="Quick and painless wrapping C code into Python",
    extras_require={
        "test": [
            'pytest>=3', 'pytest-order', 'pytest-timeout', 'toml', 'coverage',
            'coverage-conditional-plugin', 'pytest-cov', 'wheel'
        ]
    },
    license="MIT license",
    long_description=readme,
    keywords='cslug',
    name='cslug',
    packages=find_packages(include=['cslug', 'cslug.*']),
    package_data={"cslug": ["stdlib.json"]},
    test_suite='tests',
    url='https://github.com/bwoodsend/cslug',
    version=runpy.run_path("cslug/_version.py")["__version__"],
    zip_safe=True,
)
