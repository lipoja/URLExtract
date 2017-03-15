URLExtract
----------

URLExtract is python class for collecting (extracting) URLs from given
text.

.. image:: https://img.shields.io/travis/lipoja/URLExtract/master.svg
    :target: https://travis-ci.org/lipoja/URLExtract
    :alt: Build Status
.. image:: https://img.shields.io/github/tag/lipoja/URLExtract.svg
    :target: https://github.com/lipoja/URLExtract/tags
    :alt: Git tag
.. image:: https://img.shields.io/pypi/pyversions/urlextract.svg
    :target: https://pypi.python.org/pypi/urlextract
    :alt: Python Version Compatibility


How does it work
~~~~~~~~~~~~~~~~

It tries to find any occurrence of TLD in given text. If TLD is found it
starts from that position to expand boundaries to both sides searching
for "stop character" (usually whitespace, comma, single or double
quote).

NOTE: List of TLDs is downloaded from iana.org to keep you up to date with new TLDs.

Installation
~~~~~~~~~~~~

Package is available on PyPI - you can install it via pip.

.. image:: https://img.shields.io/pypi/v/urlextract.svg
    :target: https://pypi.python.org/pypi/urlextract
.. image:: https://img.shields.io/pypi/status/urlextract.svg
    :target: https://pypi.python.org/pypi/urlextract
::

   pip install urlextract

Documentation
~~~~~~~~~~~~~

Online documentation is published at http://urlextract.readthedocs.io/


Requirements
~~~~~~~~~~~~

- IDNA for converting links to IDNA format
- uritools for domain name validation

   ::

       pip install idna
       pip install uritools

Example
~~~~~~~

You can look at command line program *bin/urlextract*.
But everything you need to know is this:

.. code:: python

    from urlextract import URLExtract

    extractor = URLExtract()
    urls = extractor.find_urls("Text with URLs. Let's have URL janlipovsky.cz as an example.")
    print(urls) # prints: ['janlipovsky.cz']

License
~~~~~~~

This piece of code is licensed under The MIT License.
