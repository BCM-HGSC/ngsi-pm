#! /usr/bin/env python3

"""
Read a cram_worklist TSV for single lanes and output the barcode comparison results.
Compare CRAM RG barcodes and samples to cram_worklist barcodes and samples.
"""

# First come standard libraries, in alphabetical order.
import argparse
from collections import Counter
import logging
import os
from pathlib import Path
import re
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
    run_cram_qc(input_file)
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


def run_cram_qc(input_file):
    """input_file is XLSX workbook."""
    logger.debug('input_file: %r', input_file)
    input_path = Path(input_file)
    process_input(input_path)
    logger.debug('finished')
    # TODO
    # return error_code or results


def process_input(input_path):
    """Read the TSV input for a batch of CRAMs, barcodes and samples.
    Process CRAMs to dump RGs and verify that CRAM header barcodes and samples are 
    consistent with TSV barcodes and samples"""
    logger.debug('process_input %s', input_path)
    sl_crams = read_input(input_path)
    logger.info('found %s records', len(sl_crams))
    logger.debug('first record: %r', vars(sl_crams[0]))
    logger.debug('last record: %r', vars(sl_crams[-1]))
    pass


def read_input(input_path):
    """Read TSV input and return list of objects containing the file paths"""
    assert input_path.suffix == '.tsv'
    row_iter = generate_tsv_rows(input_path)
    column_names = next(row_iter)
    sl_crams = []
    for column_name, value in zip(column_names, row):
        if column_name in ['sample_id_nwd_id', 'lane_barcode', 'cram_path']:
            setattr(sl_cram, column_name, value)
        sl_crams.append(sl_cram)
    return sl_crams


def generate_tsv_rows(input_path):
    """Generator function that yield rows as lists of values from the TSV."""
    with open(input_path) as fin:
        for raw_line in fin:
            yield raw_line.rstrip('\r\n').split('\t')


def compare_barcodes_samples(cram_paths, lane_barcodes, sample_id_nwd_id):
    """Compare a set of CRAM RG barcodes & samples to TSV barcodes & samples for 
    a single lane sample."""
    pass


def process_cram(cram_path):
    """Read header of CRAM, parse resulting RGs and then return
    CRAM RG barcodes and CRAM RG samples"""
    rg_lines = dump_cram_rgs(cram_path)
    pass

def dump_cram_rgs(cram_path):
    """Read cram_path using samtools and return list of RG lines."""
    logger.debug('samtools view -H %r', cram_path)
    cp = run(['samtools', 'view', '-H', cram_path]
            stdin=DEVNULL, stdout=PIPE,
            universal_newlines=True)
    if cp.returncode:
        break
    headers = cp.stdout.splitlines()
    rg_lines = [h for h in headers if h.startswith('@RG\t')]
    return rg_lines


class Generic:
    """To create objects with __dict__."""
    pass


if __name__ == '__main__':
    main()
