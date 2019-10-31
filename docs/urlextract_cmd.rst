urlextract - command line
=========================

urlextract - command line program that will print all URLs to stdout

Usage: ``$ urlextract [-h] [-v] [-u] [-i <ignore_file>] [-c <config_file>] <input_file>``

positional arguments:
    <input_file> input text file with URLs to extract

optional arguments:
    -h, --help     show this help message and exit
    -v, --version  show program's version number and exit
    -u, --unique   print out only unique URLs found in file
    -i <ignore_file>, --ignore-file <ignore_file>
                   input text file with URLs to exclude from extraction
    -c <config_file>, --config-file <config_file>
                   config file for setting urlextract as JSON.
                   (see example below)

Config file example:

.. highlight::javascript

    {
        "update_when_older": 30,
        "stop_chars_left": {'\"', '<', '>', ';', '|', '=', ']', ')', '}'},
        "stop_chars_right": {'\"', '<', '>', ';'},
        "after_tld_chars": {'/', '\"', '\'', '<', '>', '?', ':', '.', ','}
        "extract_email": false
    }
