#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cachefile.py - file with classes handling cached TLDs (e.g. downloads, updates)

.. Licence MIT
.. codeauthor:: Jan Lipovský <janlipovsky@gmail.com>, janlipovsky.cz
.. contributors: https://github.com/lipoja/URLExtract/graphs/contributors
"""

import logging
import os
import tempfile
import urllib.request
from datetime import datetime
from urllib.error import URLError, HTTPError

import idna
import filelock
from appdirs import user_cache_dir


class CacheFileError(Exception):
    """
    Raised when some error occurred regarding file with cached TLDs.
    """
    pass


class CacheFile:
    """
    Class for working with cached TLDs in file.
    """

    # file name of cached list of TLDs downloaded from IANA
    _CACHE_FILE_NAME = 'tlds-alpha-by-domain.txt'
    _DATA_DIR = 'data'

    # name used in appdir
    _URLEXTRACT_NAME = "urlextract"

    def __init__(self, cache_dir=None):
        """
        :param str cache_dir: base path for TLD cache, defaults to data dir
        :raises: CacheFileError when cached file is not readable for user
        """

        self._logger = logging.getLogger(self._URLEXTRACT_NAME)

        self._user_defined_cache_dir = cache_dir
        self._default_cache_file = False

        # full path for cached file with list of TLDs
        self._tld_list_path = self._get_cache_file_path()
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
            try:
                os.makedirs(dir_path_user, exist_ok=True)
            except PermissionError:
                # if PermissionError exception is raised we should continue
                # and try to set the last fallback dir
                pass

        if os.access(dir_path_user, os.W_OK):
            return dir_path_user

        dir_path_temp = tempfile.gettempdir()
        if os.access(dir_path_temp, os.W_OK):
            return dir_path_temp

        raise CacheFileError("Cache directories are not writable.")

    def _get_cache_file_path(self):
        """
        Get path for cache file

        :raises: CacheFileError when cached directory is not writable for user
        :return: Full path to cached file with TLDs
        :rtype: str
        """
        if self._user_defined_cache_dir is None:
            # Tries to get writable cache dir with fallback to users data dir
            # and temp directory
            cache_dir = self._get_writable_cache_dir()
        else:
            cache_dir = self._user_defined_cache_dir
            if not os.access(self._user_defined_cache_dir, os.W_OK):
                raise CacheFileError(
                    "Cache directory {} is not writable.".format(
                        self._user_defined_cache_dir
                    )
                )

        # get path for cached file
        return os.path.join(cache_dir, self._CACHE_FILE_NAME)

    def _get_cache_lock_file_path(self):
        """
        Get path for cache file lock

        :raises: CacheFileError when cached directory is not writable for user
        :return: Full path to cached file lock
        :rtype: str
        """
        return self._get_cache_file_path()+'.lock'

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

        if os.path.exists(self._tld_list_path) and \
                os.access(self._tld_list_path, os.F_OK) and \
                not os.access(self._tld_list_path, os.W_OK):
            self._logger.error("ERROR: Cache file is not writable for current "
                               "user. ({})".format(self._tld_list_path))
            return False

        req = urllib.request.Request(url_list)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.0; '
                                     'WOW64; rv:24.0) Gecko/20100101 '
                                     'Firefox/24.0')
        try:
            with urllib.request.urlopen(req) as f:
                page = f.read().decode('utf-8')
        except HTTPError as e:
            self._logger.error("ERROR: Can not download list of TLDs. "
                               "(HTTPError: {})".format(e.reason))
            return False
        except URLError as e:
            self._logger.error("ERROR: Can not download list of TLDs. "
                               "(URLError: {})".format(e.reason))
            return False

        with filelock.FileLock(self._get_cache_lock_file_path()):
            with open(self._tld_list_path, 'w') as ftld:
                ftld.write(page)

        return True

    def _load_cached_tlds(self):
        """
        Loads TLDs from cached file to set.

        :return: Set of current TLDs
        :rtype: set
        """

        # check if cached file is readable
        if not os.access(self._tld_list_path, os.R_OK):
            self._logger.error("Cached file is not readable for current "
                               "user. ({})".format(self._tld_list_path))
            raise CacheFileError(
                "Cached file is not readable for current user."
            )

        set_of_tlds = set()

        with filelock.FileLock(self._get_cache_lock_file_path()):
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
