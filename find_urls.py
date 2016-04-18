#!/usr/bin/python3
# --------------------------------
# Project:  find_urls
# Author:   Jan Lipovský, 2016
# E-mail:   janlipovsky@gmail.com
# Licence:  MIT
# --------------------------------

"""
 Example of usage URLFinder. Program will print all URLs to stdout
"""
import argparse
import sys

from URLFinder import URLFinder


def get_args():
    """
    Parse programs arguments
    :return:
    """
    parser = argparse.ArgumentParser(description='url_founder - find all URLs in file')

    parser.add_argument(type=str, default=None, metavar='<input_file>', dest='input_file',
                        help='Text file where we want to find URLs. [UTF-8]')

    parsed_args = parser.parse_args()

    if parsed_args.input_file is None and parsed_args.url is None:
        print("ERROR: Please set input file")
        sys.exit(-1)

    return parsed_args


if __name__ == '__main__':
    args = get_args()

    finder = URLFinder()

    # force update of list of TLDs
    finder.update()

    # get list of stop chars - characters are determining when we should stop looking around and return found URL
    stop_chars = finder.get_stop_chars()
    # add ';' to stop chars
    stop_chars.append(';')
    finder.set_stop_chars(stop_chars)

    with open(args.input_file, "r", encoding="UTF-8") as f:
        for line in f:
            for link in finder.find_urls(line):
                print(link)
