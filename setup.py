#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup for urlextract

.. Created on 2016-07-29
.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
.. contributors: https://github.com/lipoja/URLExtract/graphs/contributors
"""

from os.path import join, dirname
from setuptools import setup, find_packages

script_dirname = join(dirname(__file__))

# version of URLExtract
# (do not forget to change it in urlextract_core.py as well)
__version__ = '1.3.0'


def read(readme):
    return open(join(script_dirname, readme), "rb").read().decode("utf-8")


setup(
    name='urlextract',
    version=__version__,
    py_modules=['urlextract'],
    entry_points={
        'console_scripts': [
            'urlextract = urlextract:_urlextract_cli'
        ]
    },
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
    keywords=[
        'url', 'extract', 'find', 'finder',
        'collect', 'link', 'tld', 'list'
    ],
    url='https://github.com/lipoja/URLExtract',
    project_urls={
        "Documentation": "https://urlextract.readthedocs.io/en/latest/",
        "Source Code": "https://github.com/lipoja/URLExtract",
    },
    license='MIT',
    author='Jan Lipovský',
    author_email='janlipovsky@gmail.com',
    description='Collects and extracts URLs from given text.',
    long_description=read('README.rst'),
    long_description_content_type='text/x-rst',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Text Processing',
        "Topic :: Text Processing :: Markup :: HTML",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=[
        'idna',
        'uritools',
        'appdirs',
        'filelock'
    ],
)
