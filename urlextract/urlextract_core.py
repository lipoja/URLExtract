#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
urlextract_core.py - file with definition of URLExtract class and urlextract cli

.. Created on 2016-07-29
.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
.. contributors: https://github.com/lipoja/URLExtract/graphs/contributors
"""
import functools
import ipaddress
import logging
import re
import socket
import string
import sys
from collections import OrderedDict
from datetime import datetime, timedelta

import uritools

from urlextract.cachefile import CacheFileError, CacheFile

# version of URLExtract (do not forget to change it in setup.py as well)
__version__ = '1.3.0'

# default value for maximum count of processed URLs by find_url
DEFAULT_LIMIT = 10000


class URLExtract(CacheFile):
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
    # compiled regexp for naive validation of host name
    _hostname_re = re.compile(
        r"^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])$")

    # list of enclosure of URL that should be removed
    _enclosure = {
        ("(", ")"),
        ("{", "}"),
        ("[", "]"),
        ("\"", "\""),
        ("\\", "\\"),
        ("'", "'"),
        ("`", "`"),
    }

    _ipv4_tld = ['.{}'.format(ip) for ip in reversed(range(256))]
    _ignore_list = set()

    _limit = DEFAULT_LIMIT

    def __init__(
            self,
            extract_email=False,
            cache_dns=True,
            extract_localhost=True,
            limit=DEFAULT_LIMIT,
            **kwargs
    ):
        """
        Initialize function for URLExtract class.
        Tries to get cached TLDs, if cached file does not exist it will try
        to download new list from IANA and save it to cache file.

        :param bool extract_email: True if we want to extract email from text.
            Disabled by default
        :param bool cache_dns: True replaces socket DNS lookup with caching
            equivalent provided by dnspython.
            Enabled by default
        :param bool extract_localhost: True if we want to extract 'localhost'
            as URL from text.
            Enabled by default
        """
        super(URLExtract, self).__init__(**kwargs)

        self._tlds_re = None
        self._extract_localhost = extract_localhost
        self._extract_email = extract_email
        self._cache_dns = cache_dns
        self._limit = limit
        self._reload_tlds_from_file()

        # general stop characters
        general_stop_chars = {'\"', '<', '>', ';'}
        # defining default stop chars left
        self._stop_chars_left = set(string.whitespace)
        self._stop_chars_left |= general_stop_chars | {'|', '=', ']', ')', '}'}

        # defining default stop chars left
        self._stop_chars_right = set(string.whitespace)
        self._stop_chars_right |= general_stop_chars

        # characters that are allowed to be right after TLD
        self._after_tld_chars = self._get_after_tld_chars()

    def _get_after_tld_chars(self):
        """
        Initialize after tld characters
        """
        after_tld_chars = set(string.whitespace)
        after_tld_chars |= {'/', '\"', '\'', '<', '>', '?', ':', '.', ','}
        # get left enclosure characters
        _, right_enclosure = zip(*self._enclosure)
        # add right enclosure characters to be valid after TLD
        # for correct parsing of URL e.g. (example.com)
        after_tld_chars |= set(right_enclosure)

        return after_tld_chars

    def _reload_tlds_from_file(self):
        """
        Reloads TLDs from file and compile regexp.
        :raises: CacheFileError when cached file is not readable for user
        """

        tlds = sorted(self._load_cached_tlds(), key=len, reverse=True)
        tlds += self._ipv4_tld
        if self._extract_localhost:
            tlds.append('localhost')
        re_escaped = [re.escape(str(tld)) for tld in tlds]
        self._tlds_re = re.compile('|'.join(re_escaped), flags=re.IGNORECASE)

    @property
    def extract_email(self):
        """
        If set to True email will be extracted from text

        :rtype: bool
        """
        return self._extract_email

    @extract_email.setter
    def extract_email(self, extract):
        """
        Set if emails will be extracted from text

        :param bool extract: True if emails should be extracted False otherwise
        """
        self._extract_email = extract

    @property
    def extract_localhost(self):
        """
        If set to True 'localhost' will be extracted as URL from text

        :rtype: bool
        """
        return self._extract_localhost

    @extract_localhost.setter
    def extract_localhost(self, enable):
        """
        Set if 'localhost' will be extracted as URL from text

        :param bool enable: True if localhost' should be extracted
            False otherwise
        """
        self._extract_localhost = enable

    @property
    def ignore_list(self):
        """
        Returns set of URLs on ignore list

        :return: Returns set of ignored URLs
        :rtype: set(str)
        """
        return self._ignore_list

    @ignore_list.setter
    def ignore_list(self, ignore_list):
        """
        Set of URLs to be ignored (not returned) while extracting from text

        :param set(str) ignore_list: set of URLs
        """
        self._ignore_list = ignore_list

    def load_ignore_list(self, file_name):
        """
        Load URLs from file into ignore list

        :param str file_name: path to file containing URLs
        """
        with open(file_name) as f:
            for line in f:
                url = line.strip()
                if not url:
                    continue
                self._ignore_list.add(url)

    def update(self):
        """
        Update TLD list cache file.

        :return: True if update was successful False otherwise
        :rtype: bool
        """
        if not self._download_tlds_list():
            return False

        self._reload_tlds_from_file()

        return True

    def update_when_older(self, days):
        """
        Update TLD list cache file if the list is older than
        number of days given in parameter `days` or if does not exist.

        :param int days: number of days from last change
        :return: True if update was successful, False otherwise
        :rtype: bool
        """

        last_cache = self._get_last_cachefile_modification()
        if last_cache is None:
            return self.update()

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

        return __version__

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

    def get_enclosures(self):
        """
        Returns set of enclosure pairs that might be used to enclosure URL.
        For example brackets (example.com), [example.com], {example.com}

        :return: set of tuple of enclosure characters
        :rtype: set(tuple(str,str))
        """
        return self._enclosure

    def add_enclosure(self, left_char, right_char):
        """
        Add new enclosure pair of characters. That and should be removed
        when their presence is detected at beginning and end of found URL

        :param str left_char: left character of enclosure pair - e.g. "("
        :param str right_char: right character of enclosure pair - e.g. ")"
        """
        assert len(left_char) == 1, \
            "Parameter left_char must be character not string"
        assert len(right_char) == 1, \
            "Parameter right_char must be character not string"
        self._enclosure.add((left_char, right_char))

        self._after_tld_chars = self._get_after_tld_chars()

    def remove_enclosure(self, left_char, right_char):
        """
        Remove enclosure pair from set of enclosures.

        :param str left_char: left character of enclosure pair - e.g. "("
        :param str right_char: right character of enclosure pair - e.g. ")"
        """
        assert len(left_char) == 1, \
            "Parameter left_char must be character not string"
        assert len(right_char) == 1, \
            "Parameter right_char must be character not string"
        rm_enclosure = (left_char, right_char)
        if rm_enclosure in self._enclosure:
            self._enclosure.remove(rm_enclosure)

        self._after_tld_chars = self._get_after_tld_chars()

    def _complete_url(self, text, tld_pos, tld, check_dns=False):
        """
        Expand string in both sides to match whole URL.

        :param str text: text where we want to find URL
        :param int tld_pos: position of TLD
        :param str tld: matched TLD which should be in text
        :param bool check_dns: filter results to valid domains
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
        temp_tlds = {tld + c for c in self._after_tld_chars}
        # get only dot+tld+one_char and compare
        extended_tld = complete_url[len(complete_url)-len(tld)-1:]
        if extended_tld in temp_tlds:
            # We do not want o change found URL
            if not extended_tld.endswith('/'):
                complete_url = complete_url[:-1]

        complete_url = self._split_markdown(complete_url, tld_pos-start_pos)
        complete_url = self._remove_enclosure_from_url(
            complete_url, tld_pos-start_pos, tld)

        # search for enclosures before URL ignoring space character " "
        # when URL contains right enclosure character (issue #77)
        enclosure_map = {
            left_char: right_char
            for left_char, right_char in self._enclosure
        }
        if any(enclosure in complete_url[tld_pos-start_pos:]
               for enclosure in enclosure_map.values()):
            enclosure_space_char = True
            enclosure_found = False
            tmp_start_pos = start_pos
            while enclosure_space_char:
                if tmp_start_pos <= 0:
                    break
                if text[tmp_start_pos - 1] == ' ':
                    tmp_start_pos -= 1
                elif text[tmp_start_pos - 1] in enclosure_map.keys():
                    tmp_start_pos -= 1
                    enclosure_found = True
                else:
                    enclosure_space_char = False

            if enclosure_found:
                pre_url = text[tmp_start_pos: start_pos]
                extended_complete_url = pre_url + complete_url
                complete_url = self._remove_enclosure_from_url(
                    extended_complete_url, tld_pos - tmp_start_pos, tld)
        # URL should not start/end with whitespace
        complete_url = complete_url.strip()
        if not self._is_domain_valid(complete_url, tld, check_dns):
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
        if tld_pos > len(text):
            return False

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

    def _is_domain_valid(self, url, tld, check_dns=False):
        """
        Checks if given URL has valid domain name (ignores subdomains)

        :param str url: complete URL that we want to check
        :param str tld: TLD that should be found at the end of URL (hostname)
        :param bool check_dns: filter results to valid domains
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
        if scheme_pos == -1:
            url = 'http://' + url
            added_schema = True
        else:
            added_schema = False

        url_parts = uritools.urisplit(url)
        # <scheme>://<authority>/<path>?<query>#<fragment>

        # if URI contains user info and schema was automatically added
        # the url is probably an email
        if url_parts.getuserinfo() and added_schema:
            # do not collect emails
            if not self._extract_email:
                return False
            else:
                # if we want to extract email we have to be sure that it
                # really is email -> given URL does not have other parts
                if (
                        url_parts.getport()
                        or url_parts.getpath()
                        or url_parts.getquery()
                        or url_parts.getfragment()
                ):
                    return False

        try:
            host = url_parts.gethost()
        except ValueError:
            self._logger.info(
                "Invalid host '%s'. "
                "If the host is valid report a bug.", url
            )
            return False

        if not host:
            return False

        if host in self._ignore_list:
            return False

        # IP address are valid hosts
        is_ipv4 = isinstance(host, ipaddress.IPv4Address)
        if is_ipv4:
            return True

        # when TLD is a number the host must be IP
        if tld in self._ipv4_tld and not is_ipv4:
            return False

        host_parts = host.split('.')

        if self._extract_localhost and host_parts == ['localhost']:
            return True

        if len(host_parts) <= 1:
            return False

        host_tld = '.'+host_parts[-1]
        if host_tld.lower() != tld.lower():
            return False

        top = host_parts[-2]

        if self._hostname_re.match(top) is None:
            return False

        if check_dns:
            if self._cache_dns is True:
                dns_cache_install()
                self._cache_dns = False

            try:
                socket.gethostbyname(host)
            except socket.herror as err:
                if err.errno == 0:
                    self._logger.info("Unable to resolve address {}: {}"
                                      .format(host, err))
                else:
                    self._logger.info(err)
                return False
            except Exception as err:
                self._logger.info(
                    "Unknown exception during gethostbyname({}) {!r}"
                    .format(host, err))
                return False

        return True

    def _remove_enclosure_from_url(self, text_url, tld_pos, tld):
        """
        Removes enclosure characters from URL given in text_url.
        For example: (example.com) -> example.com

        :param str text_url: text with URL that we want to extract from
        enclosure of two characters
        :param int tld_pos: position of TLD in text_url
        :param str tld: matched TLD which should be in text
        :return: URL that has removed enclosure
        :rtype: str
        """

        enclosure_map = {
            left_char: right_char
            for left_char, right_char in self._enclosure
        }
        # get position of most right left_char of enclosure pairs
        left_pos = max([
            text_url.rfind(left_char, 0, tld_pos)
            for left_char in enclosure_map.keys()
        ])
        left_char = text_url[left_pos] if left_pos >= 0 else ''
        right_char = enclosure_map.get(left_char, '')
        # get count of left and right enclosure characters and
        left_char_count = text_url[:left_pos+1].count(left_char)
        right_char_count = text_url[left_pos:].count(right_char)
        # we want to find only pairs and ignore rest (more occurrences)
        min_count = min(left_char_count, right_char_count)

        right_pos = len(text_url)+1
        # find position of Nth occurrence of right enclosure character
        for i in range(max(min_count, 1)):
            right_pos = text_url[:right_pos].rfind(right_char)

        if right_pos < 0 or right_pos < tld_pos:
            right_pos = len(text_url)

        new_url = text_url[left_pos + 1:right_pos]
        tld_pos -= left_pos + 1

        # Get valid domain when we have input as: example.com)/path
        # we assume that if there is enclosure character after TLD it is
        # the end URL it self therefore we remove the rest
        after_tld_pos = tld_pos + len(tld)
        if after_tld_pos < len(new_url):
            if new_url[after_tld_pos] in enclosure_map.values():
                new_url_tmp = new_url[:after_tld_pos]
                return self._remove_enclosure_from_url(
                    new_url_tmp, tld_pos, tld)

        return new_url

    @staticmethod
    def _split_markdown(text_url, tld_pos):
        """
        Split markdown URL. There is an issue wen Markdown URL is found.
        Parsing of the URL does not stop on right place so wrongly found URL
        has to be split.

        :param str text_url: URL that we want to extract from enclosure
        :param int tld_pos: position of TLD
        :return: URL that has removed enclosure
        :rtype: str
        """
        # Markdown url can looks like:
        # [http://example.com/](http://example.com/status/210)

        left_bracket_pos = text_url.find('[')
        # subtract 3 because URL is never shorter than 3 characters
        if left_bracket_pos > tld_pos-3:
            return text_url

        right_bracket_pos = text_url.find(')')
        if right_bracket_pos < tld_pos:
            return text_url

        middle_pos = text_url.rfind("](")
        if middle_pos > tld_pos:
            return text_url[left_bracket_pos+1:middle_pos]
        return text_url

    def gen_urls(self, text, check_dns=False, get_indices=False):
        """
        Creates generator over found URLs in given text.

        :param str text: text where we want to find URLs
        :param bool check_dns: filter results to valid domains
        :param bool get_indices: whether to return beginning and
            ending indices as (<url>, (idx_begin, idx_end))
        :yields: URL or URL with indices found in text or empty string if nothing was found
        :rtype: str|tuple(str, tuple(int, int))
        """
        tld_pos = 0
        matched_tlds = self._tlds_re.findall(text)

        while matched_tlds:
            tld = matched_tlds.pop(0)
            tmp_text = text[tld_pos:]
            offset = tld_pos
            tld_pos = tmp_text.find(tld)
            validated = self._validate_tld_match(text, tld, offset + tld_pos)
            if tld_pos != -1 and validated:
                tmp_url = self._complete_url(text, offset + tld_pos, tld,
                                             check_dns)
                if tmp_url:
                    # do not search for TLD in already extracted URL
                    tld_pos_url = tmp_url.find(tld)
                    # move cursor right after found TLD
                    tld_pos += len(tld) + offset
                    # move cursor after end of found URL
                    rest_url = tmp_url[tld_pos_url + len(tld):]
                    tld_pos += len(rest_url)

                    # remove all matched TLDs that were found in currently
                    # extracted URL (tmp_url resp. rest_url)
                    while matched_tlds:
                        new_tld = matched_tlds[0]
                        tmp_tld_pos_url = rest_url.find(new_tld)
                        if tmp_tld_pos_url < 0:
                            break
                        rest_url = rest_url[tmp_tld_pos_url + len(new_tld):]
                        matched_tlds.pop(0)

                    if get_indices:
                        yield tmp_url, (tld_pos - len(tmp_url), tld_pos)
                    else:
                        yield tmp_url

                    continue

            # move cursor right after found TLD
            tld_pos += len(tld) + offset

    def find_urls(self, text, only_unique=False, check_dns=False, get_indices=False):
        """
        Find all URLs in given text.

        :param str text: text where we want to find URLs
        :param bool only_unique: return only unique URLs
        :param bool check_dns: filter results to valid domains
        :return: list of URLs found in text
        :param bool get_indices: whether to return beginning and
            ending indices as (<url>, (idx_begin, idx_end))
        :rtype: list

        :raises URLExtractError: Raised when count of found URLs reaches
            given limit. Processed URLs are returned in `data` argument.
        """
        urls = self.gen_urls(text, check_dns, get_indices)
        if self._limit is None:
            if only_unique:
                return list(OrderedDict.fromkeys(urls))
            return list(urls)

        result_urls = []
        url = next(urls, '')
        url_count = 1
        while url:
            if url_count > self._limit:
                err = "Limit for extracting URLs was reached. [{} URLs]".format(
                    self._limit)
                self._logger.error(err)

                raise URLExtractError(err, data=result_urls)

            result_urls.append(url)
            url = next(urls, '')
            url_count += 1

        if only_unique:
            return list(OrderedDict.fromkeys(result_urls))
        return result_urls

    def has_urls(self, text, check_dns=False):
        """
        Checks if text contains any valid URL.
        Returns True if text contains at least one URL.

        >>> extractor = URLExtract()
        >>> extractor.has_urls("Get unique URL from: http://janlipovsky.cz")
        True

        >>> extractor.has_urls("Clean text")
        False

        :param text: text where we want to find URLs
        :param bool check_dns: filter results to valid domains
        :return: True if et least one URL was found, False otherwise
        :rtype: bool
        """

        return any(self.gen_urls(text, check_dns))


class URLExtractError(Exception):
    """
    Raised when some error occurred during processing URLs.

    Attributes:
        message -- explanation of the error
        data -- input expression in which the error occurred
    """
    def __init__(self, message, data):
        self.data = data
        self.message = message


def report_issue(func):
    """Friendly message with link to GitHub for easier reporting"""
    @functools.wraps(func)
    def wrapper_urlextract_cli(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            print(
                "Error: An unexpected error occurred. "
                "If you can not resolve this issue please report it to: "
                "https://github.com/lipoja/URLExtract/issues "
                "and help us improve urlextract!",
                file=sys.stderr)
            raise

    return wrapper_urlextract_cli


@report_issue
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
            help='print out only unique URLs found in file')

        parser.add_argument(
            "-dl", "--disable-localhost", dest='disable_localhost',
            action='store_true', help='disable extracting "localhost" as URL')

        parser.add_argument(
            "-c", "--check-dns", dest='check_dns', action='store_true',
            help='print out only URLs for existing domain names')

        parser.add_argument(
            '-i', '--ignore-file', metavar='<ignore_file>',
            type=str, default=None,
            help='input text file with URLs to exclude from extraction')

        parser.add_argument(
            "-l", "--limit", dest='limit', type=int, default=DEFAULT_LIMIT,
            help='Maximum count of URLs that can be processed. '
                 'Set 0 to disable the limit. '
                 'Default: {}'.format(DEFAULT_LIMIT)
        )

        parser.add_argument(
            'input_file', nargs='?', metavar='<input_file>',
            type=argparse.FileType(), default=sys.stdin,
            help='input text file with URLs to extract')

        parsed_args = parser.parse_args()
        return parsed_args

    args = get_args()
    logging.basicConfig(
        level=logging.WARNING, stream=sys.stderr,
        format='%(asctime)s - %(levelname)s (%(name)s): %(message)s')
    logger = logging.getLogger('urlextract')

    try:
        limit = None if args.limit <= 0 else args.limit
        urlextract = URLExtract(limit=limit)
        if args.disable_localhost:
            urlextract.extract_localhost = False
        if args.ignore_file:
            urlextract.load_ignore_list(args.ignore_file)
        urlextract.update_when_older(30)
        content = args.input_file.read()
        try:
            for url in urlextract.find_urls(content, args.unique, args.check_dns):
                print(url)
        except URLExtractError as e:
            logger.error("You can set limit using --limit parameter. "
                         "See --help for more details.")
            for url in e.data:
                print(url)

    except CacheFileError as e:
        logger.error(str(e))
        sys.exit(-1)
    finally:
        args.input_file.close()


def dns_cache_install():
    try:
        from dns_cache.resolver import ExceptionCachingResolver
        from dns import resolver as dnspython_resolver_module
        if not dnspython_resolver_module.default_resolver:
            dnspython_resolver_module.default_resolver = ExceptionCachingResolver()
        del dnspython_resolver_module
    except ImportError:
        pass

    try:
        from dns.resolver import LRUCache, Resolver, override_system_resolver, _resolver, default_resolver
    except ImportError:
        return

    if default_resolver:
        if not default_resolver.cache:
            default_resolver.cache = LRUCache()
        resolver = default_resolver
    elif _resolver and _resolver.cache:
        resolver = _resolver
    else:
        resolver = Resolver()
        resolver.cache = LRUCache()
    override_system_resolver(resolver)


if __name__ == '__main__':
    _urlextract_cli()
