#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This file contains pytests for find_urls() method of URLExtract with
list of URLs that can be processed

.. Licence MIT
.. codeauthor:: khoben <extless@gmail.com>
"""
import pytest


@pytest.mark.parametrize(
    "text, expected",
    [
        ("example.com", ["example.com"]),
        ("ample.com", []),
        ("another-url.com", ["another-url.com"]),
        ("one-another-url.com", []),
        ("http://example.com", ["http://example.com"]),
        ("http://example.com:1234", ["http://example.com:1234"]),
        (
            "http://example.com:1234 http://example.com admin@example.com example123.com",
            ["http://example.com:1234", "http://example.com"],
        ),
        ("admin@example.com", []),
        ("ftp://admin:pass@example.com", ["ftp://admin:pass@example.com"]),
        (
            "http://subdom.example.com:1234/path/file.html?query=something#hashtag",
            [],
        ),
        ("www.example.com", []),
        ("example.net", []),
    ],
)
def test_permit_list(urlextract, text, expected):
    """
    Testing find_urls with list of URLs that can be processed

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    urlextract.permit_list = {"example.com", "another-url.com"}
    assert urlextract.find_urls(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("example.com", ["example.com"]),
        ("ample.com", []),
        ("another-url.com", []),
        ("one-another-url.com", []),
        ("http://example.com", ["http://example.com"]),
        ("http://example.com:1234", ["http://example.com:1234"]),
        ("admin@example.com", []),
        ("ftp://admin:pass@example.com", ["ftp://admin:pass@example.com"]),
        (
            "http://subdom.example.com:1234/path/file.html?query=something#hashtag",
            [],
        ),
        ("www.example.com", []),
        ("example.net", []),
    ],
)
def test_permit_list_with_ignore(urlextract, text, expected):
    """
    Testing find_urls with list of URLs list that can be processed and URLs ignore list

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    urlextract.permit_list = {"example.com", "another-url.com"}
    urlextract.ignore_list = {"another-url.com"}
    assert urlextract.find_urls(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("example.com", ["example.com"]),
        ("ample.com", []),
        ("another-url.com", ["another-url.com"]),
        ("one-another-url.com", []),
        ("http://example.com", ["http://example.com"]),
        ("http://example.com:1234", ["http://example.com:1234"]),
        ("admin@example.com", ["admin@example.com"]),
        ("ftp://admin:pass@example.com", ["ftp://admin:pass@example.com"]),
        (
            "http://subdom.example.com:1234/path/file.html?query=something#hashtag",
            [],
        ),
        ("www.example.com", []),
        ("example.net", []),
    ],
)
def test_permit_list_with_emails(urlextract, text, expected):
    """
    Testing find_urls with list of URLs that can be processed with email addresses

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    urlextract.extract_email = True
    urlextract.permit_list = {"example.com", "another-url.com"}
    assert urlextract.find_urls(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        (
            "Local development url http://localhost:8000/ and www.example.com",
            ["http://localhost:8000/"],
        ),
        ("Some text with  localhost in it", []),
    ],
)
def test_host_limit_localhost_enabled(urlextract, text, expected):
    """
    Testing find_urls with list of URLs that can be processed with localhost

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    urlextract.permit_list = {"localhost"}
    assert urlextract.find_urls(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Local development url http://localhost:8000/", []),
        ("Some text with  localhost in it", []),
    ],
)
def test_host_limit_localhost_disabled(urlextract, text, expected):
    """
    Testing find_urls with list of URLs that can be processed without localhost

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    urlextract.extract_localhost = False
    urlextract.permit_list = {"localhost"}
    assert urlextract.find_urls(text) == expected
