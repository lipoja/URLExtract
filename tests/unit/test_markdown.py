#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
"""
import pytest


@pytest.mark.parametrize("text, expected", [

    ("xx[http://httpbin.org/status/200](http://httpbin.org/status/210)trololo",
     ['http://httpbin.org/status/200', 'http://httpbin.org/status/210']),

    ("This is text with markdown URL[http://httpbin.org/status/200]("
     "http://httpbin.org/status/210)",
     ['http://httpbin.org/status/200', 'http://httpbin.org/status/210']),

    ("[http://httpbin.org/status/200](http://httpbin.org/status/210)",
    ['http://httpbin.org/status/200', 'http://httpbin.org/status/210']),

])
def test_find_urls(urlextract, text, expected):
    """
    Testing find_urls returning all URLs

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    assert expected == urlextract.find_urls(text)
