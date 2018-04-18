#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This file contains pytests for find_url() method of URLExtract

.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
"""
import pytest

from urlextract import URLExtract


@pytest.fixture(scope="module")
def urlextract():
    return URLExtract()


@pytest.mark.parametrize("text, expected", [
    ("Let's have URL http://janlipovsky.cz",
     ['http://janlipovsky.cz']),

    ("Let's have text without URLs.",
     []),

    ("Dot after TLD: http://janlipovsky.cz.",
     ['http://janlipovsky.cz']),

    ("URL https://example.com/@eon01/asdsd-dummy",
     ['https://example.com/@eon01/asdsd-dummy']),

    ("ukrainian news pravda.com.ua",
     ['pravda.com.ua']),

    ("URI with User info in Authority ftp://jan@example.com:123/test",
     ['ftp://jan@example.com:123/test']),


])
def test_find_urls(urlextract, text, expected):
    """
    Testing find_urls returning all URLs

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    assert expected == urlextract.find_urls(text)


@pytest.mark.parametrize("text, expected", [
    ("http://unique.com http://unique.com",
     ['http://unique.com']),

    ("Get unique URL from: in.v_alid.cz",
     [])
])
def test_find_urls_unique(urlextract, text, expected):
    """
    Testing find_urls returning only unique URLs

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    assert urlextract.find_urls(text, only_unique=True) == expected
