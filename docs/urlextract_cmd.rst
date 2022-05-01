urlextract - command line
=========================

urlextract - command line program that will print all URLs to stdout

Usage: ``$ urlextract [-h] [-v] [-u] [-dl] [-c] [-i <ignore_file>] [-p <permit_file>] [-l LIMIT] [<input_file>]``

positional arguments:
  <input_file>          input text file with URLs to extract

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -u, --unique          print out only unique URLs found in file
  -dl, --disable-localhost
                        disable extracting "localhost" as URL
  -c, --check-dns       print out only URLs for existing domain names
  -i <ignore_file>, --ignore-file <ignore_file>
                        input text file with URLs to exclude from extraction
  -p <permit_file>, --permit-file <permit_file>
                        input text file with URLs that can be processed
  -l LIMIT, --limit LIMIT
                        Maximum count of URLs that can be processed. Set 0 to
                        disable the limit. Default: 10000
