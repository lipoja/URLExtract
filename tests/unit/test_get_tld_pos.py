#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This file contains pytests for _get_tld_pos() method of URLExtract

.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
"""
import pytest


@pytest.mark.parametrize(
    "url, tld, expected",
    [
        ("httpbin.org/status/200", ".org", 7),
        ("https://httpbin.org/status/200", ".org", 15),
        ("caseInsensitive.cOM", ".cOM", 15),
        ("https://caseInsensitive.COM/status/200", ".COM", 23),
    ],
)
def test_get_ltd_pos(urlextract, url, tld, expected):
    """
    Testing _get_tld_pos returning index

    :param fixture urlextract: fixture holding URLExtract object
    :param str url: URL in which tld should be located
    :param str tld: TLD we want to find
    :param int expected: index of tld that has be found in url
    """
    assert urlextract._get_tld_pos(url, tld) == expected
