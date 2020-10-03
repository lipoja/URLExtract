#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This file contains pytests for find_url() method of URLExtract

.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
"""
import pytest


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

    ('<a href="https://www.example.com/">example</a>',
     ['https://www.example.com/']),

    ('<a href="https://www.example.com/path/">example1</a>',
     ['https://www.example.com/path/']),

    ("https://bladomain.com/bla/?cid=74530889&h=bladomain.com",
     ['https://bladomain.com/bla/?cid=74530889&h=bladomain.com']),

    ("Hey hou we have URL containing https://example.com/what.com another URL",
     ['https://example.com/what.com']),

    ("https://i2.wp.com/siliconfilter.com/2011/06/example.jpg",
     ["https://i2.wp.com/siliconfilter.com/2011/06/example.jpg"]),

    ("https://www.test.org/paper/apostrophe'in-url",
     ["https://www.test.org/paper/apostrophe'in-url"]),

    ("http://aa.com/b.html https://aa.com/bb.html",
     ["http://aa.com/b.html", "https://aa.com/bb.html"]),

    ("http://0.0.0.0/a.io",
     ['http://0.0.0.0/a.io']),

    ("http://123.56.234.210/struts_action.do",
     ['http://123.56.234.210/struts_action.do']),
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
    ("http://caseInsensitive.cOM",
     ['http://caseInsensitive.cOM']),

    ("http://caseInsensitive.COM",
     ['http://caseInsensitive.COM']),
])
def test_find_urls_case_insensitive(urlextract, text, expected):
    """
    Testing find_urls returning only unique URLs

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    assert urlextract.find_urls(text, only_unique=True) == expected


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


@pytest.mark.parametrize("text, expected", [
    ("Let's have URL http://janlipovsky.cz and a second URL https://example.com/@eon01/asdsd-dummy it's over.",
     [('http://janlipovsky.cz', (15, 36)),
      ('https://example.com/@eon01/asdsd-dummy', (54, 92))]),
])
def test_find_urls_with_indices(urlextract, text, expected):
    """
    Testing find_urls returning only unique URLs

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    assert urlextract.find_urls(text, get_indices=True) == expected
