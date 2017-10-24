Changelog
~~~~~~~~~

- 0.7
    - Faster stop char matching
    - Fixing issue #7 by splitting stop characters to left and right. Created new methods:
        - ``get_stop_chars_left()`` and ``set_stop_chars_left()``
        - ``get_stop_chars_right()`` and set ``stop_chars_right()``
    - Deprecated:
        - ``get_stop_chars()`` and ``set_stop_chars()``
- 0.6
    - Make setup.py parsable on Python3 with LANG unset - by Dave Pretty (#6)
- 0.5
    - Fix issue #5 - URL is extracted when it ends with TLD + after_tld_chars (usually: comma, dot, ...)
- 0.4.1
    - Efficient use of memory in find_urls() method
- 0.4
    - Adding features:
        - ``has_urls()`` - returns True if in text is at least one URL
        - ``gen_urls()`` - returns generator over found URLs
- 0.3.2.6
    - Centralized version number (fixed bug when installing via pip on system where uritools are not yet installed)
- 0.3.2
    - Bug fix of incorrect validation of URL (e.g. 'http://blog/media/reflect.io.jpg') by Rui Silva
- 0.3.1
    - Adding badges to README.rst
- 0.3
    - Adding hostname validation
- 0.2.7
    - Public release