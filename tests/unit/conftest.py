#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
"""
import pytest

from urlextract import URLExtract
from dns.resolver import get_default_resolver, LRUCache


@pytest.fixture
def urlextract():
    return URLExtract()


@pytest.fixture
def dns_resolver():
    resolver = get_default_resolver()
    resolver.cache = LRUCache()
    return resolver
