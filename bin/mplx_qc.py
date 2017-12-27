#! /usr/bin/env python3

"""
Read a master XLSX workbook and output the bad merges. The output is in TSV
format and includes merge ID, CRAM path, and json path. To check the merges:
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
import re
import sys
from subprocess import run, DEVNULL, PIPE

# after a blank line, import third-party libraries.
import openpyxl

# After another blank line, import local libraries.
from dump_js_barcodes import Merge
from dump_js_barcodes import SequencingEvent

__version__ = '1.0.0-rc4'

logger = logging.getLogger(__name__)


def main():
    args = parse_args()
    config_logging(args)
    error_code = run_qc(args)
    logging.shutdown()
    sys.exit(error_code)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_file')
    parser.add_argument('-v', '--verbose', action='count')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()
    return args


def config_logging(args):
    global logger
    if not args.verbose:
        level = logging.WARNING
    elif args.verbose == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG
    logging.basicConfig(level=level)
    logger = logging.getLogger('mplx_qc')


def run_qc(args):
    logger.debug('args: %r', args)
    input_file = args.input_file
    error_code = process_input(input_file)
    logger.debug('finished')
    return error_code


def process_input(input_file):
    """Read the XLSX input for a batch of merged CRAMs. Verify that the CRAM
    headers and JSON metadata are consistent. Return an error code, where 0
    means no errors, otherwise corresponding to the most severe error."""
    logger.debug('process_input %s', input_file)
    merged_crams = read_input(input_file)
    logger.info('found %s records', len(merged_crams))
    logger.debug('first record: %r', vars(merged_crams[0]))
    logger.debug('last record: %r', vars(merged_crams[-1]))
    error_code = 0  # no error
    for record in merged_crams:
        logger.info('checking %s', record.merge_id)
        ec = compare_read_groups(record.sample_id_nwd_id,
                                 record.cram_path,
                                 record.json_path)
        if ec:
            print(ec, record.merge_id, record.cram_path, record.json_path,
                  sep='\t')
        error_code = max(error_code, ec)
    return error_code


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
            if column_name in ['sample_id_nwd_id', 'merge_id',
                               'json_path', 'cram_path']:
                value = cell.value
                setattr(merged_cram, column_name, value)
        merged_crams.append(merged_cram)
    return merged_crams


def compare_read_groups(sample_id_nwd_id, cram_path, json_path):
    """Compare a set of CRAM RG barcodes & samples to JSON barcodes & samples
    for one merged CRAM, returning most severe error code.

    Expectations:
        set(cram_rg_barcodes) == set(json_rg_barcodes)
        len(set(cram_rg_barcodes)) == len(cram_rg_barcodes)
        len(set(json_rg_barcodes)) == len(json_rg_barcodes)
        len(set(cram_rg_samples)) == len(set(json_rg_samples)) == 1
        set(cram_rg_samples) == set(json_rg_samples)
    """
    cram_rg_barcodes, cram_rg_samples = process_cram(cram_path)
    json_rg_barcodes, json_rg_samples = process_json(json_path)
    logger.info('found %s cram_rg_barcodes, %s json_rg_barcodes',
                len(cram_rg_barcodes), len(json_rg_barcodes))
    logger.debug('first barcodes: %s, %s',
                 cram_rg_barcodes[0], json_rg_barcodes[0])
    cram_rg_sample_set = set(cram_rg_samples)
    json_rg_sample_set = set(json_rg_samples)
    cram_rg_sample = next(iter(cram_rg_sample_set))
    if len(cram_rg_sample_set) != 1:
        error_code = 7
        logger.error('CRAM contains multiple values for sample. '
                     'CRAM=%r samples=%r',
                     cram_path, cram_rg_samples)
    elif cram_rg_sample != sample_id_nwd_id:
        error_code = 6
        logger.error('CRAM has wrong sample name. '
                     'CRAM=%r sample=%r expect=%r',
                     cram_path, cram_rg_sample, sample_id_nwd_id)
    elif cram_rg_sample_set != json_rg_sample_set:
        error_code = 5
        logger.error('CRAM and JSON have different sample names. '
                     'CRAM=%r JSON=%r cram_sample=%r json_sample=%r',
                     cram_path, json_path,
                     cram_rg_sample_set, json_rg_sample_set)
    elif len(set(cram_rg_barcodes)) != len(cram_rg_barcodes):
        error_code = 4  # same barcode included twice
        ctr = Counter(cram_rg_barcodes)
        duplicate_barcodes = [bc for bc, count in ctr.items() if count > 1]
        logger.error('Duplicate barcodes in CRAM. CRAM=%r dupes=%r',
                     cram_path, duplicate_barcodes)
        # TODO: Resolve duplicated code in next case.
    elif len(set(json_rg_barcodes)) != len(json_rg_barcodes):
        error_code = 3  # same barcode included twice
        ctr = Counter(json_rg_barcodes)
        duplicate_barcodes = [bc for bc, count in ctr.items() if count > 1]
        logger.error('Duplicate barcodes in JSON. JSON=%r dupes=%r',
                     json_path, duplicate_barcodes)
    elif set(cram_rg_barcodes) != set(json_rg_barcodes):
        error_code = 2
        logger.error('CRAM and JSON have mismatching sets of barcodes. '
                     'CRAM=%r JSON=%r',
                     cram_path, json_path)
    else:
        error_code = 0
    return error_code


MULTIPLE = object()  # For corrupt data with two PUs or SMs in the same RG.


def process_cram(cram_path):
    """Read header of CRAM, parse resulting RGs and then return
    CRAM RG barcodes and CRAM RG samples"""
    rg_lines = dump_cram_rgs(cram_path)
    cram_rg_barcodes = []
    cram_rg_samples = []
    for rg_line in rg_lines:
        rg_items = rg_line.rstrip().split('\t')[1:]
        pu = sm = None
        for rg_item in rg_items:
            if rg_item.startswith('PU:'):
                if pu is not None:
                    pu = MULTIPLE
                else:
                    pu = rg_item[3:]
            elif rg_item.startswith('SM:'):
                if sm is not None:
                    sm = MULTIPLE
                else:
                    sm = rg_item[3:]
        cram_rg_barcodes.append(pu)
        cram_rg_samples.append(sm)
    return cram_rg_barcodes, cram_rg_samples


def dump_cram_rgs(cram_path):
    """Read cram_path using samtools and return list of RG lines."""
    logger.debug('samtools view -H %r', cram_path)
    # TODO: Should we try to handle an error here?
    cp = run(['samtools', 'view', '-H', cram_path],
             stdin=DEVNULL, stdout=PIPE,
             universal_newlines=True, check=True)
    headers = cp.stdout.splitlines()
    rg_lines = [h for h in headers if h.startswith('@RG\t')]
    return rg_lines


def process_json(json_path):
    """from dump_js_barcodes.py import Merge,
    and parse JSON merge barcodes and JSON merge samples"""
    logger.debug('parsing: %s', json_path)
    merge = Merge(json_path)
    barcodes = [s.barcode for s in merge.sequencing_events]
    samples = [s.sample_name for s in merge.sequencing_events]
    return barcodes, samples


class Generic:
    """To create objects with __dict__."""
    pass


if __name__ == '__main__':
    main()