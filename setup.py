#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup for urlextract

.. Created on 2016-07-29
.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
"""

import os
from distutils.core import setup


def read(readme):
    return open(os.path.join(os.path.dirname(__file__), readme)).read()


setup(
    name='urlextract',
    version="0.3",
    py_modules=['urlextract'],
    scripts=['bin/urlextract'],
    keywords=['url', 'extract', 'find', 'finder', 'collect', 'link', 'tld', 'list'],
    url='https://github.com/lipoja/URLExtract',
    license='MIT',
    author='Jan Lipovský',
    author_email='janlipovsky@gmail.com',
    description='Collects and extracts URLs from given text.',
    long_description=read('README.rst'),
    classifiers=["Development Status :: 4 - Beta",
                 "Intended Audience :: Developers",
                 "License :: OSI Approved :: MIT License",
                 "Programming Language :: Python",
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: 3.6',
                 'Topic :: Text Processing',
                 "Topic :: Text Processing :: Markup :: HTML",
                 "Topic :: Software Development :: Libraries :: Python Modules",
                 ],
    install_requires=[
        'idna',
        'uritools'
    ],
)
