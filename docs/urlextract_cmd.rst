urlextract - command line
=========================

urlextract - command line program that will print all URLs to stdout

Usage: ``$ urlextract [-h] [-v] [-u] [-i <ignore_file>] <input_file>``

positional arguments:
    <input_file> input text file with URLs to extract

optional arguments:
    -h, --help     show this help message and exit
    -v, --version  show program's version number and exit
    -u, --unique   print out only unique URLs found in file
    -i <ignore_file>, --ignore-file <ignore_file>
                   input text file with URLs to exclude from extraction

