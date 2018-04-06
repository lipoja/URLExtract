#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
urlextract.py - file with definition of URLExtract class and urlextract cli

.. Created on 2016-07-29
.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
.. contributors: Rui Silva
"""
import os
import re
import string
import sys
import logging
import urllib.request
import warnings
from datetime import datetime, timedelta
from urllib.error import URLError, HTTPError

import idna
import uritools

from version import __VERSION__


class CacheFileError(Exception):
    """
    Raised when some error occurred regarding file with cached TLDs.
    """
    pass


class URLExtract:
    """
    Class for finding and extracting URLs from given string.

    **Examples:**

    .. code-block:: python

        from urlextract import URLExtract

        extractor = URLExtract()
        urls = extractor.find_urls("Let's have URL example.com example.")
        print(urls) # prints: ['example.com']

        # Another way is to get a generator over found URLs in text:
        for url in extractor.gen_urls(example_text):
            print(url) # prints: ['example.com']

        # Or if you want to just check if there is at least one URL in text:
        if extractor.has_urls(example_text):
            print("Given text contains some URL")
    """
    # file name of cached list of TLDs downloaded from IANA
    _CACHE_FILE_NAME = '.urlextract_tlds'

    def __init__(self):
        """
        Initialize function for URLExtract class.
        Tries to get cached .tlds, if cached file does not exist it will try
        to download new list from IANNA and save it to users home directory.

        :raises: CacheFileError when cached file is not readable for user
        """
        self._logger = logging.getLogger(__name__)
        # get directory for cached file
        dir_path = os.path.dirname(__file__)
        if not os.access(dir_path, os.W_OK):
            # get path to home dir
            dir_path = os.path.expanduser('~')

        # full path for cached file with list of TLDs
        self._tld_list_path = os.path.join(dir_path, self._CACHE_FILE_NAME)
        if not os.access(self._tld_list_path, os.F_OK):
            if not self._download_tlds_list():
                raise CacheFileError("Can not download list of TLDs.")

        # check if cached file is readable
        if not os.access(self._tld_list_path, os.R_OK):
            raise CacheFileError("Cached file is not readable for current "
                                 "user. ({})".format(self._tld_list_path))

        # try to update cache file when cache is older than 7 days
        if not self.update_when_older(7):
            self._logger.warning(
                "Could not update file, using old version "
                "of TLDs list. ({})".format(self._tld_list_path))

        self._tlds = None
        self._tlds_re = None
        self._reload_tlds_from_file()

        host_re_txt = "^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])$"
        self._hostname_re = re.compile(host_re_txt)

        # general stop characters
        general_stop_chars = {'\"', '\'', '<', '>', ';'}
        # defining default stop chars left
        self._stop_chars_left = set(string.whitespace)
        self._stop_chars_left |= general_stop_chars | {'|', '@', '=', '[', ']'}

        # defining default stop chars left
        self._stop_chars_right = set(string.whitespace)
        self._stop_chars_right |= general_stop_chars

        # preprocessed union _stop_chars is used in _validate_tld_match
        self._stop_chars = self._stop_chars_left | self._stop_chars_right

        # characters that are allowed to be right after TLD
        self._after_tld_chars = set(string.whitespace)
        self._after_tld_chars |= {'/', '\"', '\'', '<', '?', ':', '.', ','}

    def _reload_tlds_from_file(self):
        """
        Reloads TLDs from file and compile regexp.
        """
        # check if cached file is readable
        if not os.access(self._tld_list_path, os.R_OK):
            self._logger.error("Cached file is not readable for current "
                               "user. ({})".format(self._tld_list_path))
        else:
            self._tlds = sorted(self._load_cached_tlds(),
                                key=len, reverse=True)
            re_escaped = [re.escape(str(tld)) for tld in self._tlds]
            self._tlds_re = re.compile('|'.join(re_escaped))

    def _download_tlds_list(self):
        """
        Function downloads list of TLDs from IANA.
        LINK: https://data.iana.org/TLD/tlds-alpha-by-domain.txt

        :return: True if list was downloaded, False in case of an error
        :rtype: bool
        """
        url_list = 'https://data.iana.org/TLD/tlds-alpha-by-domain.txt'

        # check if we can write cache file
        if os.access(self._tld_list_path, os.F_OK) and \
                not os.access(self._tld_list_path, os.W_OK):
            self._logger.error("ERROR: Cache file is not writable for current "
                               "user. ({})".format(self._tld_list_path))
            return False

        req = urllib.request.Request(url_list)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.0; '
                                     'WOW64; rv:24.0) Gecko/20100101 '
                                     'Firefox/24.0')
        with open(self._tld_list_path, 'w') as ftld:
            try:
                with urllib.request.urlopen(req) as f:
                    page = f.read().decode('utf-8')
                    ftld.write(page)
            except HTTPError as e:
                self._logger.error("ERROR: Can not download list ot TLDs. "
                                   "(HTTPError: {})".format(e.reason))
                return False
            except URLError as e:
                self._logger.error("ERROR: Can not download list ot TLDs. "
                                   "(URLError: {})".format(e.reason))
                return False
        return True

    def _load_cached_tlds(self):
        """
        Loads TLDs from cached file to set.

        :return: Set of current TLDs
        :rtype: set
        """

        list_of_tlds = set()
        with open(self._tld_list_path, 'r') as f:
            for line in f:
                tld = line.strip().lower()
                # skip empty lines
                if len(tld) <= 0:
                    continue
                # skip comments
                if tld[0] == '#':
                    continue

                list_of_tlds.add("." + tld)
                list_of_tlds.add("." + idna.decode(tld))

        return list_of_tlds

    def _get_last_cachefile_modification(self):
        """
        Get last modification of cache file with TLDs.

        :return: Date and time of last modification or
                 None when file does not exist
        :rtype: datetime|None
        """

        try:
            mtime = os.path.getmtime(self._tld_list_path)
        except OSError:
            return None

        return datetime.fromtimestamp(mtime)

    def update(self):
        """
        Update TLD list cache file.

        :return: True if update was successfull False otherwise
        :rtype: bool
        """

        if not self._download_tlds_list():
            return False

        self._reload_tlds_from_file()

        return True

    def update_when_older(self, days):
        """
        Update TLD list cache file if the list is older than
        number of days given in parameter `days`.

        :param int days: number of days from last change
        :return: True if update was successfull, False otherwise
        :rtype: bool
        """

        last_cache = self._get_last_cachefile_modification()
        if last_cache is None:
            return False

        time_to_update = last_cache + timedelta(days=days)

        if datetime.now() >= time_to_update:
            return self.update()

        return True

    @staticmethod
    def get_version():
        """
        Returns version number.

        :return: version number
        :rtype: str
        """

        return __VERSION__

    def get_after_tld_chars(self):
        """
        Returns list of chars that are allowed after TLD

        :return: list of chars that are allowed after TLD
        :rtype: list
        """

        return list(self._after_tld_chars)

    def set_after_tld_chars(self, after_tld_chars):
        """
        Set chars that are allowed after TLD.

        :param list after_tld_chars: list of characters
        """

        self._after_tld_chars = set(after_tld_chars)

    def get_stop_chars(self):
        """
        Returns list of stop chars.

        .. deprecated:: 0.7
            Use :func:`get_stop_chars_left` or :func:`get_stop_chars_right`
            instead.

        :return: list of stop chars
        :rtype: list
        """
        warnings.warn("Method get_stop_chars is deprecated, "
                      "use `get_stop_chars_left` or "
                      "`get_stop_chars_right` instead", DeprecationWarning)
        return list(self._stop_chars)

    def set_stop_chars(self, stop_chars):
        """
        Set stop characters used when determining end of URL.

        .. deprecated:: 0.7
            Use :func:`set_stop_chars_left` or :func:`set_stop_chars_right`
            instead.

        :param list stop_chars: list of characters
        """

        warnings.warn("Method set_stop_chars is deprecated, "
                      "use `set_stop_chars_left` or "
                      "`set_stop_chars_right` instead", DeprecationWarning)
        self._stop_chars = set(stop_chars)
        self._stop_chars_left = self._stop_chars
        self._stop_chars_right = self._stop_chars

    def get_stop_chars_left(self):
        """
        Returns set of stop chars for text on left from TLD.

        :return: set of stop chars
        :rtype: set
        """
        return self._stop_chars_left

    def set_stop_chars_left(self, stop_chars):
        """
        Set stop characters for text on left from TLD.
        Stop characters are used when determining end of URL.

        :param set stop_chars: set of characters
        :raises: TypeError
        """
        if not isinstance(stop_chars, set):
            raise TypeError("stop_chars should be type set "
                            "but {} was given".format(type(stop_chars)))

        self._stop_chars_left = stop_chars
        self._stop_chars = self._stop_chars_left | self._stop_chars_right

    def get_stop_chars_right(self):
        """
        Returns set of stop chars for text on right from TLD.

        :return: set of stop chars
        :rtype: set
        """
        return self._stop_chars_right

    def set_stop_chars_right(self, stop_chars):
        """
        Set stop characters for text on right from TLD.
        Stop characters are used when determining end of URL.

        :param set stop_chars: set of characters
        :raises: TypeError
        """
        if not isinstance(stop_chars, set):
            raise TypeError("stop_chars should be type set "
                            "but {} was given".format(type(stop_chars)))

        self._stop_chars_right = stop_chars
        self._stop_chars = self._stop_chars_left | self._stop_chars_right

    def _complete_url(self, text, tld_pos, tld):
        """
        Expand string in both sides to match whole URL.

        :param str text: text where we want to find URL
        :param int tld_pos: position of TLD
        :param str tld: matched TLD which should be in text
        :return: returns URL
        :rtype: str
        """

        left_ok = True
        right_ok = True

        max_len = len(text) - 1
        end_pos = tld_pos
        start_pos = tld_pos
        while left_ok or right_ok:
            if left_ok:
                if start_pos <= 0:
                    left_ok = False
                else:
                    if text[start_pos - 1] not in self._stop_chars_left:
                        start_pos -= 1
                    else:
                        left_ok = False
            if right_ok:
                if end_pos >= max_len:
                    right_ok = False
                else:
                    if text[end_pos + 1] not in self._stop_chars_right:
                        end_pos += 1
                    else:
                        right_ok = False

        complete_url = text[start_pos:end_pos + 1].lstrip('/')
        # remove last character from url
        # when it is allowed character right after TLD (e.g. dot, comma)
        temp_tlds = tld.join(self._after_tld_chars)
        # get only dot+tld+one_char and compare
        if complete_url[len(complete_url)-len(tld)-1:] in temp_tlds:
            complete_url = complete_url[:-1]

        if not self._is_domain_valid(complete_url, tld):
            return ""

        return complete_url

    def _validate_tld_match(self, text, matched_tld, tld_pos):
        """
        Validate TLD match - tells if at found position is really TLD.

        :param str text: text where we want to find URLs
        :param str matched_tld: matched TLD
        :param int tld_pos: position of matched TLD
        :return: True if match is valid, False otherwise
        :rtype: bool
        """
        right_tld_pos = tld_pos + len(matched_tld)
        if len(text) > right_tld_pos:
            if text[right_tld_pos] in self._after_tld_chars:
                if tld_pos > 0 and text[tld_pos - 1] \
                        not in self._stop_chars_left:
                    return True
        else:
            if tld_pos > 0 and text[tld_pos - 1] not in self._stop_chars_left:
                return True

        return False

    def _is_domain_valid(self, url, tld):
        """
        Checks if given URL has valid domain name (ignores subdomains)

        :param str url: complete URL that we want to check
        :param str tld: TLD that should be found at the end of URL (hostname)
        :return: True if URL is valid, False otherwise
        :rtype: bool

        >>> extractor = URLExtract()
        >>> extractor._is_domain_valid("janlipovsky.cz", ".cz")
        True

        >>> extractor._is_domain_valid("https://janlipovsky.cz", ".cz")
        True

        >>> extractor._is_domain_valid("invalid.cz.", ".cz")
        False

        >>> extractor._is_domain_valid("invalid.cz,", ".cz")
        False

        >>> extractor._is_domain_valid("in.v_alid.cz", ".cz")
        False

        >>> extractor._is_domain_valid("-is.valid.cz", ".cz")
        True

        >>> extractor._is_domain_valid("not.valid-.cz", ".cz")
        False

        >>> extractor._is_domain_valid("http://blog/media/path.io.jpg", ".cz")
        False
        """

        if not url:
            return False

        scheme_pos = url.find('://')
        if scheme_pos != -1:
            url = url[scheme_pos+3:]

        url = 'http://'+url

        url_parts = uritools.urisplit(url)
        # <scheme>://<authority>/<path>?<query>#<fragment>
        host = url_parts.host
        if not host:
            return False

        host_parts = host.split('.')
        if len(host_parts) <= 1:
            return False

        host_tld = '.'+host_parts[-1]
        if host_tld != tld:
            return False

        top = host_parts[-2]

        if self._hostname_re.match(top) is None:
            return False

        return True

    def gen_urls(self, text):
        """
        Creates generator over found URLs in given text.

        :param str text: text where we want to find URLs
        :yields: URL found in text or empty string if no found
        :rtype: str
        """
        tld_pos = 0
        matched_tlds = self._tlds_re.findall(text)

        for tld in matched_tlds:
            tmp_text = text[tld_pos:]
            offset = tld_pos
            tld_pos = tmp_text.find(tld)
            validated = self._validate_tld_match(text, tld, offset + tld_pos)
            if tld_pos != -1 and validated:
                tmp_url = self._complete_url(text, offset + tld_pos, tld)
                if tmp_url:
                    yield tmp_url

            tld_pos += len(tld) + offset

    def find_urls(self, text, only_unique=False):
        """
        Find all URLs in given text.

        >>> extractor = URLExtract()
        >>> extractor.find_urls("Let's have URL http://janlipovsky.cz")
        ['http://janlipovsky.cz']

        >>> extractor.find_urls("Let's have text without URLs.")
        []

        >>> extractor.find_urls("http://unique.com http://unique.com", True)
        ['http://unique.com']

        >>> extractor.find_urls("Dot after TLD: http://janlipovsky.cz.")
        ['http://janlipovsky.cz']

        >>> extractor.find_urls("URL https://example.com/@eon01/asdsd-dummy")
        ['https://example.com/@eon01/asdsd-dummy']

        >>> extractor.find_urls("Get unique URL from: in.v_alid.cz", True)
        []

        >>> extractor.find_urls("ukrainian news pravda.com.ua")
        ['pravda.com.ua']

        :param str text: text where we want to find URLs
        :param bool only_unique: return only unique URLs
        :return: list of URLs found in text
        :rtype: list
        """
        urls = self.gen_urls(text)
        urls = set(urls) if only_unique else urls
        return list(urls)

    def has_urls(self, text):
        """
        Checks if text contains any valid URL.
        Returns True if text contains at least one URL.

        >>> extractor = URLExtract()
        >>> extractor.has_urls("Get unique URL from: http://janlipovsky.cz")
        True

        >>> extractor.has_urls("Clean text")
        False

        :param text: text where we want to find URLs
        :return: True if et least one URL was found, False otherwise
        :rtype: bool
        """

        return any(self.gen_urls(text))


def _urlextract_cli():
    """
    urlextract - command line program that will print all URLs to stdout
    Usage: urlextract [input_file] [-u] [-v]

    input_file - text file with URLs to extract
    """
    import argparse

    def get_args():
        """
        Parse programs arguments
        """
        parser = argparse.ArgumentParser(
            description='urlextract - prints out all URLs that were '
                        'found in input file or stdin based on locating '
                        'their TLDs')

        ver = URLExtract.get_version()
        parser.add_argument("-v", "--version", action="version",
                            version='%(prog)s - version {}'.format(ver))

        parser.add_argument(
            "-u", "--unique", dest='unique', action='store_true',
            help='print out only unique URLs found in file.')

        parser.add_argument(
            'input_file', nargs='?', metavar='<input_file>',
            type=argparse.FileType(encoding="UTF-8"), default=sys.stdin,
            help='input text file with URLs to extract. [UTF-8]')

        parsed_args = parser.parse_args()
        return parsed_args

    args = get_args()
    logging.basicConfig(
        level=logging.INFO, stream=sys.stderr,
        format='%(asctime)s - %(levelname)s (%(name)s): %(message)s')
    logger = logging.getLogger('urlextract')

    try:
        urlextract = URLExtract()
        content = args.input_file.read()
        for url in urlextract.find_urls(content, args.unique):
            print(url)
    except CacheFileError as e:
        logger.error(str(e))
        sys.exit(-1)
    finally:
        args.input_file.close()


if __name__ == '__main__':
    _urlextract_cli()
