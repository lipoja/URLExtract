#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup for urlextract

.. Created on 2016-07-29
.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
.. contributors:: Dave Pretty
"""

import os
from distutils.core import setup

script_dirname = os.path.join(os.path.dirname(__file__))

__VERSION__ = None
# get __VERSION__ variable from file
version_file = os.path.join(script_dirname, 'version.py')
exec(open(version_file, "rb").read().decode("utf-8"))


def read(readme):
    return open(os.path.join(script_dirname, readme), "rb").read().decode("utf-8")

setup(
    name='urlextract',
    version=__VERSION__,
    py_modules=['urlextract', 'version'],
    entry_points={
              'console_scripts': [
                  'urlextract = urlextract:_urlextract_cli'
              ]
    },

    keywords=['url', 'extract', 'find', 'finder', 'collect', 'link', 'tld', 'list'],
    url='https://github.com/lipoja/URLExtract',
    project_urls={
        "Documentation": "https://urlextract.readthedocs.io/en/latest/",
        "Source Code": "https://github.com/lipoja/URLExtract",
    },
    include_package_data=True,
    license='MIT',
    author='Jan Lipovský',
    author_email='janlipovsky@gmail.com',
    description='Collects and extracts URLs from given text.',
    long_description=read('README.rst'),
    long_description_content_type='text/x-rst',
    classifiers=["Development Status :: 4 - Beta",
                 "Intended Audience :: Developers",
                 "License :: OSI Approved :: MIT License",
                 "Programming Language :: Python",
                 'Programming Language :: Python :: 3.3',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: 3.6',
                 'Programming Language :: Python :: 3.7',
                 'Topic :: Text Processing',
                 "Topic :: Text Processing :: Markup :: HTML",
                 "Topic :: Software Development :: Libraries :: Python Modules",
                 ],
    install_requires=[
        'idna',
        'uritools',
        'appdirs'
    ],
)
