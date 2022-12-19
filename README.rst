URLExtract
----------

URLExtract is python class for collecting (extracting) URLs from given
text based on locating TLD.


.. image:: https://img.shields.io/github/actions/workflow/status/lipoja/URLExtract/python-package.yml?branch=master
    :target: https://github.com/lipoja/URLExtract/actions/workflows/python-package.yml
    :alt: Build
.. image:: https://img.shields.io/github/tag/lipoja/URLExtract.svg
    :target: https://github.com/lipoja/URLExtract/tags
    :alt: Git tag
.. image:: https://img.shields.io/pypi/pyversions/urlextract.svg
    :target: https://pypi.python.org/pypi/urlextract
    :alt: Python Version Compatibility
.. image:: https://img.shields.io/pypi/dw/urlextract
    :target: https://pypistats.org/packages/urlextract
    :alt: PyPI downloads per week
.. image:: https://img.shields.io/pypi/dm/urlextract
    :target: https://pypistats.org/packages/urlextract
    :alt: PyPI downloads   


How does it work
~~~~~~~~~~~~~~~~

It tries to find any occurrence of TLD in given text. If TLD is found it
starts from that position to expand boundaries to both sides searching
for "stop character" (usually whitespace, comma, single or double
quote).

A dns check option is available to also reject invalid domain names.

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
- platformdirs for determining user's cache directory
- dnspython to cache DNS results

   ::

       pip install idna
       pip install uritools
       pip install platformdirs
       pip install dnspython

Or you can install the requirements with `requirements.txt`:

   ::

       pip install -r requirements.txt


Run tox
~~~~~~~

Install tox:

   ::

       pip install tox

Then run it:

   ::

       tox

Example
~~~~~~~

You can look at command line program at the end of *urlextract.py*.
But everything you need to know is this:

.. code:: python

    from urlextract import URLExtract

    extractor = URLExtract()
    urls = extractor.find_urls("Text with URLs. Let's have URL janlipovsky.cz as an example.")
    print(urls) # prints: ['janlipovsky.cz']

Or you can get generator over URLs in text by:

.. code:: python

    from urlextract import URLExtract

    extractor = URLExtract()
    example_text = "Text with URLs. Let's have URL janlipovsky.cz as an example."

    for url in extractor.gen_urls(example_text):
        print(url) # prints: ['janlipovsky.cz']

Or if you want to just check if there is at least one URL you can do:

.. code:: python

    from urlextract import URLExtract

    extractor = URLExtract()
    example_text = "Text with URLs. Let's have URL janlipovsky.cz as an example."

    if extractor.has_urls(example_text):
        print("Given text contains some URL")

If you want to have up to date list of TLDs you can use ``update()``:

.. code:: python

    from urlextract import URLExtract

    extractor = URLExtract()
    extractor.update()

or ``update_when_older()`` method:

.. code:: python

    from urlextract import URLExtract

    extractor = URLExtract()
    extractor.update_when_older(7) # updates when list is older that 7 days

Known issues
~~~~~~~~~~~~

Since TLD can be not only shortcut but also some meaningful word we might see "false matches" when we are searching
for URL in some HTML pages. The false match can occur for example in css or JS when you are referring to HTML item
using its classes.

Example HTML code:

.. code-block:: html

  <p class="bold name">Jan</p>
  <style>
    p.bold.name {
      font-weight: bold;
    }
  </style>

If this HTML snippet is on the input of ``urlextract.find_urls()`` it will return ``p.bold.name`` as an URL.
Behavior of urlextract is correct, because ``.name`` is valid TLD and urlextract just see that there is ``bold.name``
valid domain name and ``p`` is valid sub-domain.

License
~~~~~~~

This piece of code is licensed under The MIT License.
