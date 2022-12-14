#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This file contains pytests for find_url() method of URLExtract

.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
"""
import pytest


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Let's have URL http://janlipovsky.cz", ["http://janlipovsky.cz"]),
        ("Let's have text without URLs.", []),
        ("Dot after TLD: http://janlipovsky.cz.", ["http://janlipovsky.cz"]),
        (
            "URL https://example.com/@eon01/asdsd-dummy",
            ["https://example.com/@eon01/asdsd-dummy"],
        ),
        ("ukrainian news pravda.com.ua", ["pravda.com.ua"]),
        (
            '<a href="https://www.example.com/">example</a>',
            ["https://www.example.com/"],
        ),
        (
            '<a href="https://www.example.com/path/">example1</a>',
            ["https://www.example.com/path/"],
        ),
        (
            "https://bladomain.com/bla/?cid=74530889&h=bladomain.com",
            ["https://bladomain.com/bla/?cid=74530889&h=bladomain.com"],
        ),
        (
            "Hey hou we have URL containing https://example.com/what.com another URL",
            ["https://example.com/what.com"],
        ),
        (
            "* test link -https://www.example.com",
            ["https://www.example.com"],
        ),
        (
            "https://www.test.org/paper/apostrophe'in-url",
            ["https://www.test.org/paper/apostrophe'in-url"],
        ),
        (
            "http://aa.com/b.html https://aa.com/bb.html",
            ["http://aa.com/b.html", "https://aa.com/bb.html"],
        ),
        ("http://0.0.0.0/a.io", ["http://0.0.0.0/a.io"]),
        (
            "http://123.56.234.210/struts_action.do",
            ["http://123.56.234.210/struts_action.do"],
        ),
        (
            "<script src='//www.example.com/somejsfile.js'>",
            ["www.example.com/somejsfile.js"],
        ),
        ("bad.email @address.net>", ['bad.email']),
        ('[[ "$(giturl)" =~ ^https://gitlab.com ]] echo "found" || echo "didnt', []),
    ],
)
def test_find_urls(urlextract, text, expected):
    """
    Testing find_urls returning all URLs

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    assert urlextract.find_urls(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("http://caseInsensitive.cOM", ["http://caseInsensitive.cOM"]),
        ("http://caseInsensitive.COM", ["http://caseInsensitive.COM"]),
    ],
)
def test_find_urls_case_insensitive(urlextract, text, expected):
    """
    Testing find_urls returning only unique URLs

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    assert urlextract.find_urls(text, only_unique=True) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("http://unique.com http://unique.com", ["http://unique.com"]),
        ("Get unique URL from: in.v_alid.cz", []),
    ],
)
def test_find_urls_unique(urlextract, text, expected):
    """
    Testing find_urls returning only unique URLs

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    assert urlextract.find_urls(text, only_unique=True) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        (
            "Let's have URL http://janlipovsky.cz and a second URL https://Example.Com/@eon01/asdsd-dummy it's over.",
            [
                ("http://janlipovsky.cz", (15, 36)),
                ("https://Example.Com/@eon01/asdsd-dummy", (54, 92)),
            ],
        ),
        (
            "Some text www.company.com",
            [
                ("www.company.com", (10, 25)),
            ],
        ),
    ],
)
def test_find_urls_with_indices(urlextract, text, expected):
    """
    Testing find_urls returning only unique URLs

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    assert urlextract.find_urls(text, get_indices=True) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Let's have URL http://janlipovsky.cz", ["http://janlipovsky.cz"]),
        ("Without schema janlipovsky.cz", []),
    ],
)
def test_find_urls_schema_only(urlextract, text, expected):
    """
    Testing find_urls returning only unique URLs

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    assert urlextract.find_urls(text, with_schema_only=True) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("multiple protocols, job:https://example.co", ["https://example.co"]),
        (
            "more multiple protocols, link:job:https://example.com/r",
            ["https://example.com/r"],
        ),
        ("svn+ssh://example.com", ["svn+ssh://example.com"]),
    ],
)
def test_find_urls_multiple_protocol(urlextract, text, expected):
    """
    Testing find_urls returning all URLs

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    assert urlextract.find_urls(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("svn+ssh://example.com", ["ssh://example.com"]),
        ("multiple protocols, job:https://example.co", ["https://example.co"]),
        ("test link:job:https://example.com/r", ["https://example.com/r"]),
    ],
)
def test_find_urls_multiple_protocol_custom(urlextract, text, expected):
    """
    Testing find_urls returning all URLs

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    stop_chars = urlextract.get_stop_chars_left_from_scheme() | {"+"}
    urlextract.set_stop_chars_left_from_scheme(stop_chars)
    assert urlextract.find_urls(text) == expected
