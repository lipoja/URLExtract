#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains pytests for exeption URLs () method of URLExtract

.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
"""
import pytest


@pytest.mark.parametrize("text, expected", [
    ("example.com", []),
    ("ample.com", ['ample.com']),
    ("another-url.com", []),
    ("http://example.com", []),
    ("http://example.com:1234", []),
    ("admin@example.com", []),
    ("ftp://admin:pass@example.com", []),
    ("http://subdom.example.com:1234/path/file.html?query=something#hashtag",
    ["http://subdom.example.com:1234/path/file.html?query=something#hashtag"]),
    ("www.example.com", ["www.example.com"]),
    ("example.net", ["example.net"]),
])
def test_ignore_list(urlextract, text, expected):
    """
    Testing filtering out URLs on ignore list

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    urlextract.ignore_list = {'example.com', 'another-url.com'}
    assert expected == urlextract.find_urls(text)
