#! /usr/bin/env python3

"""
Read a master XLSX workbook or TSV and output the bad merges. The output is in
TSV format and includes merge ID, CRAM path, and json path. To check the
merges: Read cram paths and run subprocess to output RGs, and then output RG
barcodes and samples. Parse JSON Merge objects and output merge barcodes and
samples. Compare cram RG barcodes and samples to JSON merge barcodes and
samples.
"""

# First come standard libraries, in alphabetical order.
import argparse
from collections import Counter
from json import JSONDecodeError
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
from dump_js_barcodes import MISSING_KEY

__version__ = '1.2.0'

logger = logging.getLogger(__name__)

COLUMNS_NEEDED = set('sample_id_nwd_id merge_id json_path cram_path'.split())


def main():
    args = parse_args()
    config_logging(args)
    error_code = run_qc(args.input_file)
    logging.shutdown()
    sys.exit(error_code)


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__+run_qc.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
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


def run_qc(input_file):
    """
    Error codes:
     0: no errors
     1: reserved for failed assertions (program bugs) and uncaught exceptions
     2: CRAM and JSON have mismatching sets of barcodes
     3: (not possible with current schema) Duplicate barcodes in JSON
     4: Duplicate barcodes in CRAM
     5: CRAM and JSON have different sample names
     6: CRAM has wrong sample name
     7: CRAM contains multiple values for sample
     8: unused
     9: An RG in the CRAM is missing its PU
    10: An RG in the CRAM is missing its SM
    11: unused
    12: JSON is bad (invalid as JSON)
    13: CRAM is bad (invalid as CRAM)
    14: JSON is missing
    15: CRAM is missing
    16: unused
    17: Input file has bad contents
    18: Input file has bad extension
    19: Input is not a file
    20: Input file is missing
    21: JSON is bad (invalid Merge key for 'event_id')
    22: JSON is bad (invalid Merge key for 'sequencing_events')
    23: JSON is bad (invalid Merge key for 'library_name')
    24: JSON is bad (invalid SE key for 'event_id')
    25: JSON is bad (invalid SE key for 'sample_name')
    26: JSON is bad (invalid SE key for 'library_name)
    """
    logger.debug('input_file: %r', input_file)
    input_path = Path(input_file)
    try:
        error_code = process_input(input_path)
    except GrosslyBadError as e:
        error_code = e.error_code
        logger.error(e.message)
    logger.debug('finished')
    return error_code


def process_input(input_path):
    """Read the XLSX input for a batch of merged CRAMs. Verify that the CRAM
    headers and JSON metadata are consistent. Return an error code, where 0
    means no errors, otherwise corresponding to the most severe error."""
    logger.debug('process_input %s', input_path)
    merged_crams = read_input(input_path)
    logger.info('found %s records', len(merged_crams))
    logger.debug('first record: %r', vars(merged_crams[0]))
    logger.debug('last record: %r', vars(merged_crams[-1]))
    error_code = 0  # no error
    for record in merged_crams:
        logger.info('checking %s', record.merge_id)
        try:
            ec = compare_read_groups(record.sample_id_nwd_id,
                                     record.cram_path,
                                     record.json_path)
        except GrosslyBadError as e:
            logger.error(e.message)
            ec = e.error_code
        if ec:
            print(ec, record.merge_id, record.cram_path, record.json_path,
                  sep='\t')
        error_code = max(error_code, ec)
    return error_code


def read_input(input_path):
    """Read master XLSX of merged CRAMs and return list of objects containing
    the file paths."""
    check_input_path(input_path)
    try:
        if input_path.suffix == '.xlsx':
            row_iter = generate_xlsx_rows(input_path)
        else:
            assert input_path.suffix == '.tsv'
            row_iter = generate_tsv_rows(input_path)
        column_names = next(row_iter)
    except Exception as e:
        raise GrosslyBadError(
            17,
            'Input file has bad contents: {}. {}',
            input_path,
            e
        )
    check_column_names(column_names)
    merged_crams = []
    for row in row_iter:
        merged_cram = Generic()
        for column_name, value in zip(column_names, row):
            if column_name in ['sample_id_nwd_id', 'merge_id',
                               'json_path', 'cram_path']:
                setattr(merged_cram, column_name, value)
        merged_crams.append(merged_cram)
    return merged_crams


def check_input_path(input_path):
    if not input_path.exists():
        raise GrosslyBadError(20, 'Input file is missing: {}', input_path)
    if not input_path.is_file():
        raise GrosslyBadError(19, 'Input is not a file: {}', input_path)
    if input_path.suffix not in ('.tsv', '.xlsx'):
        raise GrosslyBadError(18,
                              'Input file has bad extension: {}', input_path)


def check_column_names(column_names):
    logger.debug('columns: %s', column_names)
    missing_columns = COLUMNS_NEEDED - set(column_names)
    if missing_columns:
        raise GrosslyBadError(
            17,
            'Input file has bad contents: '
            'missing_columns={} '
            'column_names={}',
            sorted(missing_columns),
            column_names
        )


def generate_xlsx_rows(input_path):
    """Generator function that yields lists of cell values from the "smpls"
    worksheet."""
    wb = openpyxl.load_workbook(str(input_path),
                                data_only=True, read_only=True)
    sheet = wb.get_sheet_by_name('smpls')
    active_sheet = wb.active
    assert sheet == active_sheet, (sheet.title, active_sheet.title)
    logger.debug('active_sheet name: %s', active_sheet.title)
    for row in active_sheet.rows:
        yield [c.value for c in row]


def generate_tsv_rows(input_path):
    """Generator function that yields rows as lists of values from the TSV."""
    with open(str(input_path)) as fin:
        for raw_line in fin:
            yield raw_line.rstrip('\r\n').split('\t')


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
                 cram_rg_barcodes[0],
                 json_rg_barcodes[0] if json_rg_barcodes else 'MISSING')
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
        bc = sm = None
        for rg_item in rg_items:
            if rg_item.startswith('PU:'):
                if bc is not None:
                    bc = MULTIPLE
                else:
                    pat = re.compile(r'PU:(?:[\w-]+_)?([\w-]+)$')
                    match = pat.match(rg_item)
                    if match:
                        bc = match.group(1)
                    else:
                        logger.error('bad PU tag in @RG for %r, PU=%r', cram_path, rg_item)
            elif rg_item.startswith('SM:'):
                if sm is not None:
                    sm = MULTIPLE
                else:
                    sm = rg_item[3:]
        if not sm:
            raise GrosslyBadError(
                10, 'An RG in the CRAM is missing its SM: {} {}'.format(
                    cram_path, rg_items
                )
            )
        if not bc:
            raise GrosslyBadError(
                9, 'An RG in the CRAM is missing its PU: {} {}'.format(
                    cram_path, rg_items
                )
            )
        cram_rg_barcodes.append(bc)
        cram_rg_samples.append(sm)
    return cram_rg_barcodes, cram_rg_samples


def dump_cram_rgs(cram_path):
    """Read cram_path using samtools and return list of RG lines."""
    if not Path(cram_path).is_file():
        raise GrosslyBadError(15, 'CRAM is missing: {}', cram_path)
    logger.debug('samtools view -H %r', cram_path)
    cp = run(['samtools', 'view', '-H', cram_path],
             stdin=DEVNULL, stdout=PIPE,
             universal_newlines=True)
    if cp.returncode:
        raise GrosslyBadError(13, 'CRAM is bad: {}', cram_path)
    headers = cp.stdout.splitlines()
    rg_lines = [h for h in headers if h.startswith('@RG\t')]
    return rg_lines


def process_json(json_path):
    """from dump_js_barcodes.py import Merge,
    and parse JSON merge barcodes and JSON merge samples"""
    if not Path(json_path).is_file():
        raise GrosslyBadError(14, 'JSON is missing: {}', json_path)
    logger.debug('parsing: %s', json_path)
    try:
        merge = Merge(json_path)
        if merge.id == MISSING_KEY:
            raise GrosslyBadError(21, 'JSON is bad: {}', json_path)
    except JSONDecodeError as e:
        raise GrosslyBadError(12, 'JSON is bad: {}', json_path)
    barcodes = [s.barcode for s in merge.sequencing_events]
    samples = [s.sample_name for s in merge.sequencing_events]
    return barcodes, samples


class Generic:
    """To create objects with __dict__."""
    pass


class GrosslyBadError(Exception):
    """Raised when an input is grossly BAD"""
    def __init__(self, error_code, message, *args):
        self.error_code = error_code
        self.message = message.format(*args)


if __name__ == '__main__':
    main()
