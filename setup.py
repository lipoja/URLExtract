#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
setup for urlextract

.. Created on 2016-07-29
.. Licence MIT
.. codeauthor:: Jan Lipovský (janlipovsky@gmail.com), janlipovsky.cz
"""

import os
from distutils.core import setup

from urlextract import URLExtract


def read(readme):
    return open(os.path.join(os.path.dirname(__file__), readme)).read()

setup(
    name='urlextract',
    version=URLExtract.get_version(),
    packages=['urlextract'],
    scripts=['bin/urlextract'],
    keywords=['url', 'extract', 'find', 'finder', 'collect', 'link', 'tld', 'list'],
    url='https://github.com/lipoja/URLExtract',
    license='MIT',
    author='Jan Lipovský',
    author_email='janlipovsky@gmail.com',
    description='Python program and library for collecting/extracting URLs from given text.'
                'It tries to find any occurrence of TLD in given text. '
                'If TLD is found it starts from that position to expand boundaries to both sides to cover whole URL.',
    long_description=read('README.rst'),
    classifiers = ["Development Status :: 4 - Beta",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: MIT License",
                   "Programming Language :: Python",
                   'Programming Language :: Python :: 3',
                   'Topic :: Text Processing',
                   "Topic :: Text Processing :: Markup :: HTML",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   ],
)
