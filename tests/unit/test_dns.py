#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for find_url() method of URLExtract with invalid hostnames.

.. Licence MIT
.. codeauthor:: John Vandenberg <jayvdb@gmail.com>
"""
import pytest

@pytest.mark.parametrize(
    "text, expected",
    [
        ("foo a.target bar", []),
        ("foo invalid.invalid bar", []),
        ("foo 127.0.0.2 bar", ["127.0.0.2"]),
    ],
)
def test_check_dns_find_urls(urlextract, text, expected):
    """
    Testing find_urls returning all URLs in valid domains

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    assert expected == urlextract.find_urls(text, check_dns=True)
