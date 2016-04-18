#!/usr/bin/python3
# --------------------------------
# Project:  URLFinder class
# Author:   Jan Lipovský, 2016
# E-mail:   janlipovsky@gmail.com
# Licence:  MIT
# --------------------------------

import string
import idna
import re
import os
import urllib.request
from urllib.error import URLError, HTTPError
import sys
from datetime import datetime, timedelta


class URLFinder:
    """
    Main class for finding URLs in given string
    """
    # file name of cached list of TLDs downloaded from IANA
    cache_file_name = '.tlds'

    def __init__(self):
        """
        Initialize function for URLFinder class
        """
        # get directory for cached file
        dir_path = os.path.dirname(__file__)
        if not os.access(dir_path, os.W_OK):
            # get path to home dir
            dir_path = os.path.expanduser('~')

        # full path for cached file with list of TLDs
        self.tld_list_path = os.path.join(dir_path, self.cache_file_name)
        if not os.access(self.tld_list_path, os.F_OK):
            if not self.__download_tlds_list():
                sys.exit(-1)

        # check if cached file is readable
        if not os.access(self.tld_list_path, os.R_OK):
            print("ERROR: Cached file is not readable for current user. ({})".format(self.tld_list_path))
            sys.exit(-2)

        # try to  update cache file when cache is older than 7 days
        if not self.update_when_older(7):
            print("WARNING: Could not update file, using old version of tlds list. ({})".format(self.tld_list_path))

        self.tlds = None
        self.tlds_re = None
        self.__reload_tlds_from_file()

        self.stop_chars = list(string.whitespace) + ['\"', '\'', '<', '>', ';', '@']
        self.after_tld_chars = list(string.whitespace) + ['/', '\"', '\'', '<', '?']

    def __reload_tlds_from_file(self):
        """
        Reloads TLDs from file and compile regexp
        """
        # check if cached file is readable
        if not os.access(self.tld_list_path, os.R_OK):
            print("ERROR: Cached file is not readable for current user. ({})".format(self.tld_list_path))
        else:
            self.tlds = sorted(self.__load_cached_tlds(), key=len, reverse=True)
            self.tlds_re = re.compile('|'.join([re.escape(tld) for tld in self.tlds]))

    def __download_tlds_list(self):
        """
        Function downloads list of TLDs from IANA 'https://data.iana.org/TLD/tlds-alpha-by-domain.txt'

        :return: True if list was downloaded, False in case of an error
        :rtype boolean
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

    def __load_cached_tlds(self):
        """
        Loads TLDs from cached file to and array (list)

        :return: Set of current TLDs
        :rtype set
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

    def __get_last_cachefile_modification(self):
        """
        Get last modification of cache file with tlds

        :return: Date and time of last modification or None when file does not exist
        :rtype datetime|None
        """

        try:
            mtime = os.path.getmtime(self.tld_list_path)
        except OSError:
            return None

        return datetime.fromtimestamp(mtime)

    def update(self):
        """
        Update tld list - cache file

        :return True if update was successfull False otherwise
        :rtype boolean
        """

        if not self.__download_tlds_list():
            return False

        self.__reload_tlds_from_file()

        return True

    def update_when_older(self, days):
        """
        Update tld list cache file if the list is older than number of days given in parameter day

        :param int days: number of days from last change
        :return True if update was successfull False otherwise
        :rtype boolean
        """

        last_cache = self.__get_last_cachefile_modification()
        if last_cache is None:
            return False

        time_to_update = last_cache + timedelta(days=days)

        if datetime.now() >= time_to_update:
            return self.update()

        return True

    def get_stop_chars(self):
        """
        Returns list of stop chars

        :return: list of stop chars
        :rtype list
        """

        return self.stop_chars

    def set_stop_chars(self, stop_chars):
        """
        Set stop characters used when determining end of URL

        :param list stop_chars: list of characters
        """

        self.stop_chars = stop_chars

    def __complete_url(self, text, tld_pos):
        """
        Expand string in both sides to match whole URL

        :param str text: text where we want to find URL
        :param int tld_pos: position of tld
        :return: returns URL
        :rtype str
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
        return text[start_pos:end_pos+1].lstrip('//')

    def __validate_tld_match(self, text, matched_tld, tld_pos):
        """
        Validate tld match - tells if at found position is really tld

        :param str text: text where we want to find URLs
        :param str matched_tld: matched tld
        :param int tld_pos: position of matched tld
        :return True if match is valid, False otherwise
        :rtype boolean
        """
        right_tld_pos = tld_pos+len(matched_tld)
        if len(text) > right_tld_pos:
            if text[right_tld_pos] in self.after_tld_chars:
                if tld_pos > 0 and text[tld_pos - 1] not in self.stop_chars:
                    return True
        else:
            if tld_pos > 0 and text[tld_pos - 1] not in self.stop_chars:
                return True

        return False

    def find_urls(self, text, only_unique=False):
        """
        Find all URLs in given text

        :param str text: text where we want to find URLs
        :param boolean only_unique: return only unique URLs
        :return: list of URLs found in text
        :rtype list
        """
        urls = []
        tld_pos = 0
        matched_tlds = self.tlds_re.findall(text)

        for tld in matched_tlds:
            tmp_text = text[tld_pos:]
            offset = tld_pos
            tld_pos = tmp_text.find(tld)
            if tld_pos != -1 and self.__validate_tld_match(text, tld, offset+tld_pos):
                urls.append(self.__complete_url(text, offset+tld_pos))
            tld_pos += len(tld) + offset
        if only_unique:
            return list(set(urls))
        return urls
