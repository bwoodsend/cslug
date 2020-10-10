# -*- coding: utf-8 -*-
"""
"""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()


setup(
    author="Brénainn Woodsend",
    author_email='bwoodsend@gmail.com',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Quick and painless wrapping C code into Python",
    entry_points={
        'console_scripts': [
            'cslug=cslug.cli:main',
        ],
    },
    install_requires=['Click>=7.0'],
    extras_require={"test": ['pytest>=3', ]},
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='cslug',
    name='cslug',
    packages=find_packages(include=['cslug', 'cslug.*']),
    test_suite='tests',
    url='https://github.com/bwoodsend/cslug',
    version='0.1.0',
    zip_safe=True,
)
