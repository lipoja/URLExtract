#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains pytests for allow_mixed_case_hostname of URLExtract

.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
"""
import pytest


@pytest.mark.parametrize(
    "text, expected",
    [
        ("ample.com", ["ample.com"]),
        ("http://Example.COM", ["http://Example.COM"]),
        ("www.example.com", ["www.example.com"]),
        ("example.Net", ["example.Net"]),
        ("EXAMPLE.CZ", ["EXAMPLE.CZ"]),
        (
            "I am sitting outside.In the middle of nowhere.My mind is lost in thoughts!",
            ["outside.In", "nowhere.My"],
        ),
    ],
)
def test_mixed_case_defaults(urlextract, text, expected):
    """
    Testing mixed case hostname URLs

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    assert urlextract.find_urls(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("ample.com", ["ample.com"]),
        ("http://Example.COM", []),
        ("www.example.com", ["www.example.com"]),
        ("EXAMPLE.CZ", ["EXAMPLE.CZ"]),
        ("example.Net", []),
        (
            "I am sitting outside.In the middle of nowhere.My mind is lost in thoughts!",
            [],
        ),
    ],
)
def test_mixed_case_disabled(urlextract, text, expected):
    """
    Testing mixed case hostname URLs

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    urlextract.allow_mixed_case_hostname = False
    assert urlextract.find_urls(text) == expected
