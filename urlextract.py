#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
urlextract.py - file with definition of URLExtract class

.. Created on 2016-07-29
.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
"""

import os
import re
import string
import sys
import urllib.request
from datetime import datetime, timedelta
from urllib.error import URLError, HTTPError

import idna
import uritools

__VERSION__ = "0.3"  #: version of URLExtract class


class URLExtract:
    """
    Class for finding and extracting URLs from given string

    **Example**

    .. code-block:: python

        from urlextract import URLExtract

        extractor = URLExtract()
        urls = extractor.find_urls("Let's have URL janlipovsky.cz as an example.")
        print(urls) # prints: ['janlipovsky.cz']


    """
    # file name of cached list of TLDs downloaded from IANA
    cache_file_name = '.tlds'

    def __init__(self):
        """
        Initialize function for URLExtract class.
        Tries to get cached .tlds, if cached file does not exist it will try to download new list from IANNA
        and save it to users home directory.
        """
        # get directory for cached file
        dir_path = os.path.dirname(__file__)
        if not os.access(dir_path, os.W_OK):
            # get path to home dir
            dir_path = os.path.expanduser('~')

        # full path for cached file with list of TLDs
        self.tld_list_path = os.path.join(dir_path, self.cache_file_name)
        if not os.access(self.tld_list_path, os.F_OK):
            if not self._download_tlds_list():
                sys.exit(-1)

        # check if cached file is readable
        if not os.access(self.tld_list_path, os.R_OK):
            print("ERROR: Cached file is not readable for current user. ({})".format(self.tld_list_path))
            sys.exit(-2)

        # try to update cache file when cache is older than 7 days
        if not self.update_when_older(7):
            print("WARNING: Could not update file, using old version of TLDs list. ({})".format(self.tld_list_path))

        self.tlds = None
        self.tlds_re = None
        self._reload_tlds_from_file()

        self.hostname_re = re.compile("^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])$")

        self.stop_chars = list(string.whitespace) + ['\"', '\'', '<', '>', ';', '@']
        # characters that are allowed to be right after TLD
        self.after_tld_chars = list(string.whitespace) + ['/', '\"', '\'', '<', '?', ':', '.', ',']

    def _reload_tlds_from_file(self):
        """
        Reloads TLDs from file and compile regexp.
        """
        # check if cached file is readable
        if not os.access(self.tld_list_path, os.R_OK):
            print("ERROR: Cached file is not readable for current user. ({})".format(self.tld_list_path))
        else:
            self.tlds = sorted(self._load_cached_tlds(), key=len, reverse=True)
            self.tlds_re = re.compile('|'.join([re.escape(tld) for tld in self.tlds]))

    def _download_tlds_list(self):
        """
        Function downloads list of TLDs from IANA 'https://data.iana.org/TLD/tlds-alpha-by-domain.txt'.

        :return: True if list was downloaded, False in case of an error
        :rtype: bool
        """
        url_list = 'https://data.iana.org/TLD/tlds-alpha-by-domain.txt'

        # check if we can write cache file
        if os.access(self.tld_list_path, os.F_OK) and not os.access(self.tld_list_path, os.W_OK):
            print("ERROR: Cache file is not writable for current user. ({})".format(self.tld_list_path))
            return False

        req = urllib.request.Request(url_list)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0')
        with open(self.tld_list_path, 'w') as ftld:
            try:
                with urllib.request.urlopen(req) as f:
                    page = f.read().decode('utf-8')
                    ftld.write(page)
            except HTTPError as e:
                print("ERROR: Can not download list ot TLDs. (HTTPError: {})".format(e.reason))
                return False
            except URLError as e:
                print("ERROR: Can not download list ot TLDs. (URLError: {})".format(e.reason))
                return False
        return True

    def _load_cached_tlds(self):
        """
        Loads TLDs from cached file to set.

        :return: Set of current TLDs
        :rtype: set
        """

        list_of_tlds = set()
        with open(self.tld_list_path, 'r') as f:
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
        Get last modification of cache file with tlds.

        :return: Date and time of last modification or None when file does not exist
        :rtype: datetime|None
        """

        try:
            mtime = os.path.getmtime(self.tld_list_path)
        except OSError:
            return None

        return datetime.fromtimestamp(mtime)

    def update(self):
        """
        Update tld list cache file.

        :return: True if update was successfull False otherwise
        :rtype: bool
        """

        if not self._download_tlds_list():
            return False

        self._reload_tlds_from_file()

        return True

    def update_when_older(self, days):
        """
        Update tld list cache file if the list is older than number of days given in parameter `days`.

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

        return self.after_tld_chars

    def set_after_tld_chars(self, after_tld_chars):
        """
        Set chars that are allowed after TLD.

        :param list after_tld_chars: list of characters
        """

        self.after_tld_chars = after_tld_chars

    def get_stop_chars(self):
        """
        Returns list of stop chars.

        :return: list of stop chars
        :rtype: list
        """

        return self.stop_chars

    def set_stop_chars(self, stop_chars):
        """
        Set stop characters used when determining end of URL.

        :param list stop_chars: list of characters
        """

        self.stop_chars = stop_chars

    def _complete_url(self, text, tld_pos):
        """
        Expand string in both sides to match whole URL.

        :param str text: text where we want to find URL
        :param int tld_pos: position of tld
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
                    if text[start_pos - 1] not in self.stop_chars:
                        start_pos -= 1
                    else:
                        left_ok = False
            if right_ok:
                if end_pos >= max_len:
                    right_ok = False
                else:
                    if text[end_pos + 1] not in self.stop_chars:
                        end_pos += 1
                    else:
                        right_ok = False

        complete_url = text[start_pos:end_pos + 1].lstrip('/')
        if not self._is_domain_valid(complete_url):
            return ""

        return complete_url

    def _validate_tld_match(self, text, matched_tld, tld_pos):
        """
        Validate tld match - tells if at found position is really tld.

        :param str text: text where we want to find URLs
        :param str matched_tld: matched tld
        :param int tld_pos: position of matched tld
        :return: True if match is valid, False otherwise
        :rtype: bool
        """
        right_tld_pos = tld_pos + len(matched_tld)
        if len(text) > right_tld_pos:
            if text[right_tld_pos] in self.after_tld_chars:
                if tld_pos > 0 and text[tld_pos - 1] not in self.stop_chars:
                    return True
        else:
            if tld_pos > 0 and text[tld_pos - 1] not in self.stop_chars:
                return True

        return False

    def _is_domain_valid(self, url):
        """
        Checks if given URL has valid domain name (ignores subdomains)

        :param str url: text where we want to find URLs
        :return: True if URL is valid, False otherwise
        :rtype: bool

        >>> extractor = URLExtract()
        >>> extractor._is_domain_valid("janlipovsky.cz")
        True

        >>> extractor._is_domain_valid("https://janlipovsky.cz")
        True

        >>> extractor._is_domain_valid("invalid.cz.")
        False

        >>> extractor._is_domain_valid("in.v_alid.cz")
        False

        >>> extractor._is_domain_valid("-is.valid.cz")
        True

        >>> extractor._is_domain_valid("not.valid-.cz")
        False
        """

        if len(url) <= 0:
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
        if len(host) <= 1:
            return False

        tld = '.'+host_parts[-1]
        if tld not in self.tlds:
            return False

        top = host_parts[-2]

        if self.hostname_re.match(top) is None:
            return False

        return True

    def find_urls(self, text, only_unique=False):
        """
        Find all URLs in given text.

        >>> extractor = URLExtract()
        >>> extractor.find_urls("Let's have URL http://janlipovsky.cz as an example.")
        ['http://janlipovsky.cz']

        >>> extractor.find_urls("Let's have text without URLs.")
        []

        >>> extractor.find_urls("Get unique URL from: http://janlipovsky.cz http://janlipovsky.cz", True)
        ['http://janlipovsky.cz']

        :param str text: text where we want to find URLs
        :param bool only_unique: return only unique URLs
        :return: list of URLs found in text
        :rtype: list
        """
        urls = []
        tld_pos = 0
        matched_tlds = self.tlds_re.findall(text)

        for tld in matched_tlds:
            tmp_text = text[tld_pos:]
            offset = tld_pos
            tld_pos = tmp_text.find(tld)
            if tld_pos != -1 and self._validate_tld_match(text, tld, offset + tld_pos):
                urls.append(self._complete_url(text, offset + tld_pos))
            tld_pos += len(tld) + offset

        return urls if not only_unique else list(set(urls))
