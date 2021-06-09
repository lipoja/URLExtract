#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
"""
import pytest


@pytest.mark.parametrize("text, expected", [
    ("http://127.0.0.1/",
     ['http://127.0.0.1/']),

    ("http://192.168.1.1/",
     ['http://192.168.1.1/']),

    ("http://192.168.1.255/test.html",
     ['http://192.168.1.255/test.html']),

    ("http://192.168.81.255/test.html",
     ['http://192.168.81.255/test.html']),

    ("http://www.test.edu.cn@8.8.8.8:51733/hn35/",
     ['http://www.test.edu.cn@8.8.8.8:51733/hn35/']),

    # square brackets defines IPv6 and later
    # therefore only IP is returned because only valid parts is within []
    ("http://[192.168.1.1]/", ['192.168.1.1']),

    ("http://192.1.1/", [])
])
def test_find_urls(urlextract, text, expected):
    """
    Testing find_urls returning all URLs

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    assert urlextract.find_urls(text) == expected
