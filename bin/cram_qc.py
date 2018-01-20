#! /usr/bin/env python3

"""
Read a cram_worklist TSV for single lanes and output the barcode comparison results.
Compare CRAM RG barcodes and samples to cram_worklist barcodes and samples.
"""

# First come standard libraries, in alphabetical order.
import argparse
from collections import Counter
import json
import os
import sys
from subprocess import run, DEVNULL, PIPE

# after a blank line, import third-party libraries.
import openpyxl

# After another blank line, import local libraries.

__version__ = '1.0.0a0'

logger = getLogger(__name__)


def main():
    args = parse_args()
    config_logging(args)
    run_cram_qc(args.arg1, args.arg2, args.arg3)
    logging.shutdown()


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'input_file',
        help='an XLSX workbook containing a master worklist '
             'in the first worksheet'
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='increase output verbosity')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()
    return args


def config_logging(args):
    global logger
    if not args.verbose:
        level = logging.WARNING
    elif args.verbose:
        level = logging.INFO
    else:
        level = logging.DEBUG
    logging.basicConfig(level=level)
    logger = logging.getLogger('cram_qc')

def run_cram_qc(arg1, arg2, arg3):
    pass


def func1(arg1):
    """Add description here."""
    pass


def func2(arg1):
    """Add description here."""
    pass


if __name__ == '__main__':
    main()
