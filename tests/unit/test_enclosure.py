#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
"""
import pytest


@pytest.mark.parametrize("text, expected", [
    (r"{\url{http://www.google.com}}",
     ["http://www.google.com"]),
    (r"{\url{http://www.google.com/file.pdf}}",
     ["http://www.google.com/file.pdf"]),
    (r"{\url{http://www.google.com/{file.pdf}}",
     ["http://www.google.com/{file.pdf"]),
    ("a(sa\"enclosure.net/bracketext\"as)asd",
     ['enclosure.net/bracketext']),
    ("<email@address.net>",
     []),
    ("`https://coala.io/200`",
     ['https://coala.io/200']),
    ("(enclosure.net/bracket)",
     ['enclosure.net/bracket']),
    ("enclosure.net)",
     ['enclosure.net']),
    ("(enclosure.net",
     ['enclosure.net']),
    ("(enclosure.net)",
     ['enclosure.net']),
    ("(encl)o(sure.net",
     ['sure.net']),
    ("enclosure.net/blah)o(blah",
     ['enclosure.net/blah)o(blah']),
    ("(enclosure.net/blah)o(blah",
     ['enclosure.net/blah']),
    ("stackoverflow.com)/my_account",
     ['stackoverflow.com']),
    ("{enclosure.net/curly}",
     ['enclosure.net/curly']),
    ("[enclosure.net/square]",
     ['enclosure.net/square']),
    ("\"enclosure.net/dqoute\"",
     ['enclosure.net/dqoute']),
    ("\\enclosure.net/slash\\",
     ['enclosure.net/slash']),
    ("'enclosure.net/qoute'",
     ['enclosure.net/qoute']),
    ("(( example.net)asd",
     ['example.net']),
    ("asd(enclosure.net/bracketext)asd",
     ['enclosure.net/bracketext']),
    ("Foo (http://de.wikipedia.org/wiki/Agilit%C3%A4t_(Management)) Bar",
     ["http://de.wikipedia.org/wiki/Agilit%C3%A4t_(Management)"]),
    ("asd(http://de.wikipedia.org/wiki/(Agilit%C3(%A4t_(Manag)ement))) Bar",
     ["http://de.wikipedia.org/wiki/(Agilit%C3(%A4t_(Manag)ement))"]),
    ("asd(enclosure.net/rbracketless",
     ['enclosure.net/rbracketless']),
    ("asd)enclosure.net/lbracketless",
     ['enclosure.net/lbracketless']),
    ("asd{enclosure.net",
     ['enclosure.net']),
    ("asd}enclosure.net",
     ['enclosure.net']),
    ("asd[enclosure.net",
     ['enclosure.net']),
    ("asd]enclosure.net",
     ['enclosure.net']),
    ("(enclo(sure.net",
     ['sure.net']),
    ('([smh.com.au])]',
     ['smh.com.au']),
    ('"some string with urls ( example.com/somepath)"',
     ['example.com/somepath']),
    ('"some string with urls example.com/somepa)th)"',
     ['example.com/somepa)th)']),
    ("asd( enclosure.net/bracketext)asd",
     ['enclosure.net/bracketext']),
])
def test_find_urls(urlextract, text, expected):
    """
    Testing find_urls returning all URLs

    :param fixture urlextract: fixture holding URLExtract object
    :param str text: text in which we should find links
    :param list(str) expected: list of URLs that has to be found in text
    """
    assert urlextract.find_urls(text) == expected


def test_get_enclosures(urlextract):
    assert urlextract._enclosure == urlextract.get_enclosures()


def test_add_enclosure(urlextract):

    old_enclosure = urlextract.get_enclosures().copy()
    old_enclosure.add(("%", "%"))
    urlextract.add_enclosure("%", "%")

    assert old_enclosure == urlextract.get_enclosures()

    with pytest.raises(AssertionError):
        urlextract.remove_enclosure("aa", "ss")

    with pytest.raises(AssertionError):
        urlextract.remove_enclosure("", "")


def test_remove_enclosure(urlextract):
    old_enclosure = urlextract.get_enclosures().copy()
    old_enclosure.remove(("%", "%"))
    urlextract.remove_enclosure("%", "%")

    assert old_enclosure == urlextract.get_enclosures()

    with pytest.raises(AssertionError):
        urlextract.remove_enclosure("asd", "dddsa")

    with pytest.raises(AssertionError):
        urlextract.remove_enclosure("", "")
