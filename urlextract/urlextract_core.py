#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
urlextract_core.py - file with definition of URLExtract class and urlextract cli

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
import tempfile
import urllib.request
import warnings
from datetime import datetime, timedelta
from urllib.error import URLError, HTTPError
from appdirs import user_cache_dir

import idna
import uritools

# version of URLExtract (do not forget to change it in setup.py as well)
__version__ = '0.9'


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
    _CACHE_FILE_NAME = 'tlds-alpha-by-domain.txt'
    _DATA_DIR = 'data'

    # compiled regexp for naive validation of host name
    _hostname_re = re.compile(
        "^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])$")

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

    # name used in appdir
    _URLEXTRACT_NAME = "urlextract"

    def __init__(self, cache_dir=None):
        """
        Initialize function for URLExtract class.
        Tries to get cached TLDs, if cached file does not exist it will try
        to download new list from IANA and save it to users home directory.

        :param str cache_dir: base path for TLD cache, defaults to data dir
        :raises: CacheFileError when cached file is not readable for user
        """
        self._logger = logging.getLogger(__name__)

        # True if user specified path to cache directory
        self._user_defined_cache = bool(cache_dir)
        self._default_cache_file = False

        # full path for cached file with list of TLDs
        self._tld_list_path = self._get_cache_file_path(cache_dir)
        if not os.access(self._tld_list_path, os.F_OK):
            self._logger.info(
                "Cache file not found in '%s'. "
                "Use URLExtract.update() to download newest version.",
                self._tld_list_path)
            self._logger.info(
                "Using default list of TLDs provided in urlextract package."
            )
            self._tld_list_path = self._get_default_cache_file_path()
            self._default_cache_file = True

        self._tlds_re = None
        self._reload_tlds_from_file()

        # general stop characters
        general_stop_chars = {'\"', '\'', '<', '>', ';'}
        # defining default stop chars left
        self._stop_chars_left = set(string.whitespace)
        self._stop_chars_left |= general_stop_chars | {'|', '=', ']', ')', '}'}

        # defining default stop chars left
        self._stop_chars_right = set(string.whitespace)
        self._stop_chars_right |= general_stop_chars

        # preprocessed union _stop_chars is used in _validate_tld_match
        self._stop_chars = self._stop_chars_left | self._stop_chars_right

        # characters that are allowed to be right after TLD
        self._after_tld_chars = self._get_after_tld_chars()

    def _get_default_cache_dir(self):
        """
        Returns default cache directory (data directory)

        :raises: CacheFileError when default cached file does not is exist
        :return: path to default cache directory
        :rtype: str
        """

        return os.path.join(os.path.dirname(__file__), self._DATA_DIR)

    def _get_default_cache_file_path(self):
        """
        Returns default cache file path

        :return: default cache file path (to data directory)
        :rtype: str
        """

        default_list_path = os.path.join(
            self._get_default_cache_dir(), self._CACHE_FILE_NAME)

        if not os.access(default_list_path, os.F_OK):
            raise CacheFileError(
                "Default cache file does not exist "
                "'{}'!".format(default_list_path)
            )

        return default_list_path

    def _get_writable_cache_dir(self):
        """
        Get writable cache directory with fallback to user's cache directory
        and global temp directory

        :raises: CacheFileError when cached directory is not writable for user
        :return: path to cache directory
        :rtype: str
        """
        dir_path_data = self._get_default_cache_dir()

        if os.access(dir_path_data, os.W_OK):
            self._default_cache_file = True
            return dir_path_data

        dir_path_user = user_cache_dir(self._URLEXTRACT_NAME)
        if not os.path.exists(dir_path_user):
            os.makedirs(dir_path_user, exist_ok=True)

        if os.access(dir_path_user, os.W_OK):
            return dir_path_user

        dir_path_temp = tempfile.gettempdir()
        if os.access(dir_path_temp, os.W_OK):
            return dir_path_temp

        raise CacheFileError("Cache directories are not writable.")

    def _get_cache_file_path(self, cache_dir=None):
        """
        Get path for cache file

        :param str cache_dir: base path for TLD cache, defaults to data dir
        :raises: CacheFileError when cached directory is not writable for user
        :return: Full path to cached file with TLDs
        :rtype: str
        """
        if cache_dir is None:
            # Tries to get writable cache dir with fallback to users data dir
            # and temp directory
            cache_dir = self._get_writable_cache_dir()
        else:
            if not os.access(cache_dir, os.W_OK):
                raise CacheFileError("None of cache directories is writable.")

        # get directory for cached file
        return os.path.join(cache_dir, self._CACHE_FILE_NAME)

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
        # check if cached file is readable
        if not os.access(self._tld_list_path, os.R_OK):
            self._logger.error("Cached file is not readable for current "
                               "user. ({})".format(self._tld_list_path))
            raise CacheFileError(
                "Cached file is not readable for current user."
            )
        else:
            tlds = sorted(self._load_cached_tlds(), key=len, reverse=True)
            re_escaped = [re.escape(str(tld)) for tld in tlds]
            self._tlds_re = re.compile('|'.join(re_escaped))

    def _download_tlds_list(self):
        """
        Function downloads list of TLDs from IANA.
        LINK: https://data.iana.org/TLD/tlds-alpha-by-domain.txt

        :return: True if list was downloaded, False in case of an error
        :rtype: bool
        """
        url_list = 'https://data.iana.org/TLD/tlds-alpha-by-domain.txt'

        # Default cache file exist (set by _default_cache_file)
        # and we want to write permission
        if self._default_cache_file and \
                not os.access(self._tld_list_path, os.W_OK):
            self._logger.info("Default cache file is not writable.")
            self._tld_list_path = self._get_cache_file_path()
            self._logger.info(
                "Changed path of cache file to: %s",
                self._tld_list_path
            )

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

        set_of_tlds = set()
        with open(self._tld_list_path, 'r') as f_cache_tld:
            for line in f_cache_tld:
                tld = line.strip().lower()
                # skip empty lines
                if not tld:
                    continue
                # skip comments
                if tld[0] == '#':
                    continue

                set_of_tlds.add("." + tld)
                set_of_tlds.add("." + idna.decode(tld))

        return set_of_tlds

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
        temp_tlds = {tld + c for c in self._after_tld_chars}
        # get only dot+tld+one_char and compare
        if complete_url[len(complete_url)-len(tld)-1:] in temp_tlds:
            complete_url = complete_url[:-1]

        complete_url = self._split_markdown(complete_url, tld_pos-start_pos)
        complete_url = self._remove_enclosure_from_url(
            complete_url, tld_pos-start_pos, tld)
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
        if scheme_pos == -1:
            url = 'http://' + url

        url_parts = uritools.urisplit(url)
        # <scheme>://<authority>/<path>?<query>#<fragment>

        host = url_parts.gethost()
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

        for left_char, right_char in self._enclosure:
            left_pos = text_url.find(left_char)
            if left_pos < 0 or left_pos > tld_pos:
                continue

            right_pos = text_url.rfind(right_char)
            if right_pos < 0:
                right_pos = len(text_url)

            if right_pos < tld_pos:
                continue

            new_url = text_url[left_pos + 1:right_pos]
            return self._remove_enclosure_from_url(
                new_url, tld_pos - left_pos, tld)

        # Get valid domain when we have input as: example.com)/path
        # we assume that if there is enclosure character after TLD it is
        # the end URL it self therefore we remove the rest
        after_tld_pos = tld_pos + len(tld)
        if after_tld_pos < len(text_url):
            right_enclosures = {right_e for _, right_e in self._enclosure}
            if text_url[after_tld_pos] in right_enclosures:
                new_url = text_url[:after_tld_pos]
                return self._remove_enclosure_from_url(
                    new_url, tld_pos, tld)

        return text_url

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
        urlextract.update_when_older(30)
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
