#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This file contains pytests for find_url() method of URLExtract

.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
"""
import pytest

from urlextract.urlextract_core import URLExtractError


@pytest.mark.parametrize("limit", (2, None))
@pytest.mark.parametrize("text, expected", [
    ("Let's have URL http://janlipovsky.cz",
     ['http://janlipovsky.cz']),

    ("http://aa.com/b.html https://aa.com/bb.html",
     ["http://aa.com/b.html", "https://aa.com/bb.html"]),
])
def test_find_urls_with_limit_success(urlextract, text, expected, limit):
    """
    Testing find_urls returning all URLs

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    urlextract._limit = limit
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
    urlextract._limit = 2
    assert urlextract.find_urls(text, only_unique=True) == expected


@pytest.mark.parametrize("text, expected", [
    ("http://aa.com/b.html https://aa.com/bb.html",
     ["http://aa.com/b.html"]),
])
def test_find_urls_with_limit_raised(urlextract, text, expected):
    """
    Testing find_urls returning all URLs

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    urlextract._limit = 1
    with pytest.raises(URLExtractError) as e:
        urlextract.find_urls(text)
        assert expected == e.data
