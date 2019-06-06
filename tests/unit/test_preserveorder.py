#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
"""
import pytest


@pytest.mark.parametrize("text, expected", [

    ("yahoo.com msn.com yahoo.com",
     ['yahoo.com', 'msn.com', 'yahoo.com'])

])
def test_find_urls(urlextract, text, expected):
    """
    Testing find_urls returning all URLs in the order they exist (or exists first) in the input text.

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    assert expected == urlextract.find_urls(text)


@pytest.mark.parametrize("text, expected", [

    ("yahoo.com msn.com yahoo.com msn.com msn.com",
     ['yahoo.com', 'msn.com'])

])
def test_find_urls(urlextract, text, expected):
    """
    Testing find_urls returning unique URLs in the order they exist (or exists first) in the input text.

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    assert expected == urlextract.find_urls(text, only_unique=True)
