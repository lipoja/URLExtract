#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
"""
import pytest


@pytest.mark.parametrize("text, expected", [
    ("URI with User info in Authority ftp://jan@example.com:123/test",
     ['ftp://jan@example.com:123/test']),

    ("<email@address.net>",
     []),

    ("Do not extract emails by default jan@example.com",
     []),
])
def test_extract_email_disabled(urlextract, text, expected):
    """
    Testing find_urls *NOT* returning email addresses from text

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    assert expected == urlextract.find_urls(text)


@pytest.mark.parametrize("text, expected", [
    ("Do not extract emails by default jan@example.com",
     ['jan@example.com']),

    ("<email@address.net>",
     ['email@address.net']),

    ("Given URIs are not mail jan@example.com/asdasd jan@example.com:1234",
     []),

    ("Given URIs are not mail jan@example.com?not jan@example.com#not",
     []),

])
def test_extract_email_enabled(urlextract, text, expected):
    """
    Testing find_urls returning all email addresses from text

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    urlextract.extract_email = True
    assert expected == urlextract.find_urls(text)
