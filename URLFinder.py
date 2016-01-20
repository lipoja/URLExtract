#!/usr/bin/python3
# --------------------------------
# Project:  URLFinder class
# Author:   Jan Lipovský, 2016
# E-mail:   janlipovsky@gmail.com
# Licence:  MIT
# --------------------------------

import tldextract
import string
import idna
import re


class URLFinder:
    """
    Main class for finding URLs in given string
    """
    def __init__(self):
        """
        Initialize function for URLFinder class
        :return:
        """
        tmp_tlds = {"."+(str(tld).strip('!*.')) for tld in tldextract.TLDExtract()._get_tld_extractor().tlds}
        tmp_idna_tlds = {"."+idna.encode(tld).decode('utf-8') for tld in tmp_tlds}
        self.tlds = sorted(tmp_idna_tlds.union(tmp_tlds), key=len, reverse=True)
        # escaped = [re.escape(tld) for tld in self.tlds]
        self.tlds_re = re.compile('|'.join([re.escape(tld) for tld in self.tlds]))
        self.stop_chars = list(string.whitespace) + ['\"', '\'', '<', '>', ';']
        self.after_tld_chars = list(string.whitespace) + ['/']

    def _complete_url(self, text, tld_pos):
        """
        Expand string in both sides to match whole URL
        :param text: text where we want to find URL
        :param tld_pos: position of tld
        :return: returns URL
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

    def _validate_tld_match(self, text, matched_tld, tld_pos):
        """
        Valide tld match - tells if at found position is really tld
        :param text: text where we want to find URLs
        :param matched_tld: matched tld
        :param tld_pos: position of matched tld
        :return:
        """
        right_tld_pos = tld_pos+len(matched_tld)
        if len(text) > right_tld_pos and text[right_tld_pos] in self.after_tld_chars:
            end_ok = True
        else:
            end_ok = False

        if tld_pos > 0 and text[tld_pos-1] not in self.stop_chars:
            start_ok = True
        else:
            start_ok = False

        return end_ok and start_ok

    def find_urls(self, text, only_unique=False):
        """
        Find all URLs in given text
        :param text: text where we want to find URLs
        :param boolean only_unique: return only unique URLs
        :return: list of URLs
        """
        urls = []
        tld_pos = 0
        matched_tlds = self.tlds_re.findall(text)

        for tld in matched_tlds:
            tmp_text = text[tld_pos:]
            offset = tld_pos
            tld_pos = tmp_text.find(tld)
            if tld_pos != -1 and self._validate_tld_match(text, tld, offset+tld_pos):
                urls.append(self._complete_url(text, offset+tld_pos))
            tld_pos += len(tld) + offset
        if only_unique:
            return list(set(urls))
        return urls
