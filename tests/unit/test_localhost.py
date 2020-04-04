#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
"""
import pytest


@pytest.mark.parametrize("text, expected", [
    ("Local development url http://localhost:8000/",
     ['http://localhost:8000/']),

    ("Some text with localhost in it", []),
])
def test_extractlocalhost(urlextract, text, expected):
    """
    Testing extracting localhost from test

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    assert expected == urlextract.find_urls(text)


@pytest.mark.parametrize("text, expected", [
    ("Local development url http://localhost:8000/", []),
    ("Some text with  localhost in it", []),
])
def test_extract_localhost_disabled(urlextract, text, expected):
    """
    Testing disabled extracting of localhost from test

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    urlextract.extract_localhost = False
    assert expected == urlextract.find_urls(text)
