URLExtract
----------

URLExtract is python class for collecting (extracting) URLs from given
text.

How does it work
~~~~~~~~~~~~~~~~

It tries to find any occurrence of TLD in given text. If TLD is found it
starts from that position to expand boundaries to both sides searching
for "stop character" (usually whitespace, comma, single or double
quote).

Installation
~~~~~~~~~~~~

Package is available on pypi sou you can install it via pip.

::

   pip install urlextract

Documentation
~~~~~~~~~~~~~

Online documentation is published at http://urlextract.readthedocs.io/


Requirements
~~~~~~~~~~~~

-  IDNA for converting links to IDNA format

   ::

       pip install idna

Example
~~~~~~~

You can look at command line program *bin/urlextract*.
But everything you need to know is this:

.. code:: python

    from URLExtract import URLExtract

    extractor = URLExtract()
    urls = extractor.find_urls("Text with URLs. Let's have URL janlipovsky.cz as an example.")
    print(urls) # prints: ['janlipovsky.cz']

License
~~~~~~~

This piece of code is licensed under The MIT License.
