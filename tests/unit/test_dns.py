#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for find_url() method of URLExtract with invalid hostnames.

.. Licence MIT
.. codeauthor:: John Vandenberg <jayvdb@gmail.com>
"""
import pytest

import dns.resolver
try:
    from dns_cache.resolver import ExceptionCachingResolver
except ImportError:
    ExceptionCachingResolver = None

import urlextract.urlextract_core as urlextract_core
from urlextract import URLExtract


def test_check_dns_disabled(urlextract):
    """
    Testing no network, including dns, is used by default
    """
    socket_module = urlextract_core.socket

    urlextract._cache_dns = False
    try:
        urlextract_core.socket = None

        results = urlextract.find_urls("https://github.com")
        assert len(results) == 1
        results = urlextract.find_urls("https://github.com", check_dns=False)
        assert len(results) == 1
    finally:
        urlextract_core.socket = socket_module


def test_check_dns_enabled(urlextract):
    """
    Testing network is used when check_dns is enabled
    """
    socket_module = urlextract_core.socket
    network_used = False

    urlextract._cache_dns = False
    try:
        urlextract_core.socket = None

        urlextract.find_urls("https://github.com", check_dns=True)
    except AttributeError:
        network_used = True
    finally:
        urlextract_core.socket = socket_module

    assert network_used

    urlextract._cache_dns = True
    try:
        urlextract_core.socket = None

        urlextract.find_urls("https://github.com", check_dns=True)
    except AttributeError:
        network_used = True
    finally:
        urlextract_core.socket = socket_module

    assert network_used


def test_dns_cache_init():
    """
    Testing creating a new DNS caching resolver
    """
    default_resolver = dns.resolver.get_default_resolver()
    assert default_resolver == dns.resolver.default_resolver
    if default_resolver:
        dns.resolver.default_resolver = None

    underscore_resolver = dns.resolver._resolver
    if underscore_resolver:
        dns.resolver._resolver = None

    urlextract = URLExtract()
    assert dns.resolver.default_resolver is None
    assert dns.resolver._resolver is None

    results = urlextract.find_urls("https://github.com", check_dns=True)
    assert len(results) == 1

    if not ExceptionCachingResolver:
        assert dns.resolver.default_resolver is None

    resolver = dns.resolver._resolver
    assert resolver is not None
    assert resolver.cache is not None
    assert resolver.cache.data is not None
    assert len(resolver.cache.data) == 1


def test_dns_cache_reuse():
    """
    Testing re-using an existing DNS caching resolver
    """
    underscore_resolver = dns.resolver._resolver
    if underscore_resolver:
        dns.resolver._resolver = None

    default_resolver = dns.resolver.get_default_resolver()
    if ExceptionCachingResolver:
        assert default_resolver.__class__ == ExceptionCachingResolver

    assert default_resolver == dns.resolver.default_resolver
    cache = dns.resolver.LRUCache()
    default_resolver.cache = cache

    urlextract = URLExtract()
    assert dns.resolver._resolver is None

    results = urlextract.find_urls("https://github.com", check_dns=True)
    assert len(results) == 1

    assert dns.resolver._resolver is not None
    assert dns.resolver.default_resolver == default_resolver
    assert dns.resolver.default_resolver.cache == cache

    assert default_resolver.cache.data is not None
    assert len(default_resolver.cache.data) == 1


def test_dns_cache_negative(urlextract, dns_resolver):
    """
    Testing negative results are not cached
    """
    if ExceptionCachingResolver:
        assert dns_resolver.__class__ == ExceptionCachingResolver

    # https://github.com/rthalley/dnspython/pull/238 isnt merged
    results = urlextract.find_urls("https://github.com", check_dns=True)
    assert len(results) == 1
    assert len(dns_resolver.cache.data) == 1

    results = urlextract.find_urls("https://bitbucket.org", check_dns=True)
    assert len(results) == 1
    assert len(dns_resolver.cache.data) == 2

    results = urlextract.find_urls("https://al.fr", check_dns=True)
    assert len(results) == 0
    if ExceptionCachingResolver:
        assert dns_resolver.__class__ == ExceptionCachingResolver
        assert len(dns_resolver.cache.data) == 3
    else:
        assert len(dns_resolver.cache.data) == 2


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
