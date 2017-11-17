#! /usr/bin/env python3

"""
Read a master XLSX workbook and output cram paths and json paths.
Read cram paths and run subprocess to output RGs, and then output RG barcodes
and samples. Parse JSON Merge objects and output merge barcodes and samples.
Compare cram RG barcodes and samples to JSON merge barcodes and samples.
"""

# First come standard libraries, in alphabetical order.
import argparse
from collections import Counter
import json
import logging
import os
from pathlib import Path
import pprint
import sys
from subprocess import run, DEVNULL, PIPE

# after a blank line, import third-party libraries.
import openpyxl
from openpyxl.styles import Font

# After another blank line, import local libraries.
from dump_js_barcodes import Merge
from dump_js_barcodes import SequencingEvent

__version__ = '1.0.0-working'

logger = logging.getLogger(__name__)


def main():
    args = parse_args()
    config_logging(args)
    run(args)
    logging.shutdown()


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_file',
                        nargs='?',
                        type=argparse.FileType('rb'),
                        default=sys.stdin)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()
    return args


def config_logging(args):
    global logger
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level)
    logger = logging.getLogger('mplx_qc')


def run(args):
    logger.debug('args: %r', args)
    input_file = args.input_file
    # read_input(input_file)
    merged_crams = read_input(input_file)
    # process_json_data(json_paths)
    process_input(merged_crams)
    logger.debug('finished')


def process_json_data(json_paths):
    """from dump_js_barcodes.py import Merge,
    and parse JSON merge barcodes and JSON merge samples"""
    logger.debug('seaching: %s', json_paths)
    for merge in parse_merge_definition(json_path_stream):
        for s in merge.sequencing_events:
            row = [s.barcode, s.sample_name]
            print(*row, sep='\t')
    

def parse_merge_definition(json_path_stream):
    """json_path_stream is also known as json_paths, 
    Generator of Merge objects."""
    logger.debug('generating %s', 'Merge objects')
    for line in json_path_stream:
        json_path = line.rstrip('\n')
        merge = Merge(json_path)
        yield merge


def process_cram(cram_paths):
    """Read cram_paths, run samtools to parse
    CRAM barcodes and CRAM samples"""
    logger.debug('seching: %s', cram_paths)
    pass


def compare_barcodes(json_barcodes, cram_barcodes):
    """Compare the set of JSON barcodes and samples to
    the set of CRAM barcodes and samples"""
    logger.debug('searching: %s and %s', json_barcodes, cram_barcodes)
    pass


def process_input(merged_crams):
    """Read merged_crams and output json_paths and cram_paths"""
    logger.debug('processing %s', merged_crams)
    merge_dict = {}
    for line in merged_crams:
        pass


def read_input(input_file):
    """Read master XLSX of merged CRAMs and return list of objects containing
    the file paths."""
    wb = openpyxl.load_workbook(filename=input_file)
    sheet = wb.get_sheet_by_name('smpls')
    active_sheet = wb.active
    assert sheet == active_sheet, (sheet.title, active_sheet.title)
    logger.debug('active_sheet name: %s', active_sheet.title)
    row_iter = iter(active_sheet.rows)
    header_row = next(row_iter)
    column_names = [c.value for c in header_row]
    logger.debug('columns: %s', column_names)
    merged_crams = []
    for row in row_iter:
        merged_cram = Generic()
        for column_name, cell in zip(column_names, row):
            if column_name in ['json_path', 'cram_path']:
                value = cell.value
                setattr(merged_cram, column_name, value)
        merged_crams.append(merged_cram)

    logger.info('type: %s', type(merged_crams))
    logger.info('found %s records', len(merged_crams))
    pprint.pprint(vars(merged_crams[0]))
    return merged_crams
    # sys.exit()


class Generic:
    """To create objects with __dict__."""
    pass


if __name__ == '__main__':
    main()
