from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

setup(
    author="Brénainn Woodsend",
    author_email='bwoodsend@gmail.com',
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    description="Quick and painless wrapping C code into Python",
    extras_require={
        "test": [
            'pytest>=3', 'pytest-timeout', 'toml', 'coverage',
            'coverage-conditional-plugin', 'wheel',
            'pytest_ordered @ https://github.com/bwoodsend/pytest-ordered/archive/480e13c0c23ca8f4601f18aff9990f42935cc8c4.zip'
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
    version="0.7.0",
    zip_safe=True,
)
