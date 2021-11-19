#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This file contains pytests for has_url() method of URLExtract

.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
"""
import pytest


@pytest.mark.parametrize(
    "text, expected, with_schema",
    [
        ("Get unique URL from: http://janlipovsky.cz", True, False),
        ("Text without URL", False, False),
        ("example.com", True, False),
        ("example.com", False, True),
    ],
)
def test_has_urls(urlextract, text, expected, with_schema):
    """
    Testing has_urls returning all URLs

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: expected result
    """
    assert urlextract.has_urls(text, with_schema_only=with_schema) is expected
