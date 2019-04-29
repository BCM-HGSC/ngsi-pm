#!/usr/bin/env python3

"""To create VCF WORKLIST.
Read a master workbook and output an TSV file."""

# First come standard libraries, in alphabetical order.
import argparse
import csv
import logging
import os
import pprint
import sys
import warnings
from pathlib import Path

# After a blank line, import third-party libraries.
import openpyxl

# After another blank line, import local libraries.

# Since this script has been used with no known issue in production,
# deleting the "-unstable" suffix.
# Hgv19 feature will be added to the script,
# so changing the version to 1.1.0
__version__ = '1.1.0'

logger = logging.getLogger(__name__)

REQUIRED_INPUT_COLUMN_NAMES = '''
    sample_id/nwd_id
    merge_id
    vcf_batch
    merge_path
'''.split()  # The order of the columns in the output
REQUIRED_INPUT_COLUMN_NAMES_SET = set(REQUIRED_INPUT_COLUMN_NAMES)
ADDITIONAL_OUTPUT_COLUMN_NAMES = '''
    snp_file
    snp_path
    indel_file
    indel_path
'''.split()  # The order of the columns in the output

# Extensions, useful when there are many extensions
SNP_PATTERNS = 'variants/*_snp_Annotated.vcf', 'variants/xAtlas/*_snp.vcf.gz'
SNP_EXT = '_snp_Annotated.vcf', '_snp.vcf.gz'
INDEL_PATTERNS = 'variants/*_indel_Annotated.vcf', 'variants/xAtlas/*_indel.vcf.gz'
INDEL_EXT = '_indel_Annotated.vcf', '_indel.vcf.gz'


def main():
    args = parse_args()
    config_logging(args)
    run(args)
    logging.shutdown()


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'input_file',
        help='an XLSX workbook containing a master worklist '
            'in the first worksheet'
    )
    parser.add_argument('-o', '--output_file',
                        help='will default to MASTER_vcf.tsv')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='increase output verbosity')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()
    if args.output_file is None:
        args.output_file = munge_input_file_name(args.input_file)
    return args


def munge_input_file_name(input_file_name):
    """X.xlsx -> X_vcf.tsv"""
    assert input_file_name.endswith('.xlsx')
    return input_file_name[:-5] + '_vcf.tsv'


def config_logging(args):
    global logger
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level)
    logger = logging.getLogger('vcf_worklist')


def run(args):
    logger.debug('args: %r', args)
    input_file = args.input_file
    output_file = args.output_file
    process_input(input_file, output_file)
    logger.debug('finished')


def process_input(input_file, output_file):
    """A docstring should say something about the inputs, operation,
    and any return values. In this case there are no return values,
    since results are printed to the specified file."""
    logger.debug('process_input %s -> %s', input_file, output_file)
    data = read_input(input_file)
    logger.info('found %s records', len(data))
    for record in data:
        add_file_paths(record)
    pprint.pprint(vars(data[0]))
    write_annotated_workbook(output_file, data)


def read_input(input_file):
    """Return representation of reading master XLSX."""
    warnings.simplefilter("ignore")
    wb = openpyxl.load_workbook(filename=input_file)
    master_worksheet = find_master_worksheet(wb)
    logger.debug('master worksheet name: %s', master_worksheet.title)
    row_iter = iter(master_worksheet.rows)
    header_row = next(row_iter)
    column_names = [c.value for c in header_row]
    logger.debug('columns: %s', column_names)
    missing = set(REQUIRED_INPUT_COLUMN_NAMES) - set(column_names)
    assert not missing, 'missing: {}'.format(sorted(missing))
    data = []
    for row in row_iter:
        record = Generic()
        for column_name, cell in zip(column_names, row):
            if column_name in REQUIRED_INPUT_COLUMN_NAMES_SET:
                value = cell.value
                setattr(record, column_name, value)
        if record.merge_path and record.merge_path[0] != '#':
            data.append(record)
    return data


def find_master_worksheet(wb):
    master_worksheet = None
    for ws in wb:
        logger.debug('found: %s', ws.title)
        if ws.title.endswith('_smpls') or ws.title == 'smpls':
            assert master_worksheet is None, 'ambiguous worksheets: {}, {}'.format(
                master_worksheet.title, ws.title
            )
            master_worksheet = ws
    assert master_worksheet, 'no worksheet with correct name'
    return master_worksheet


def add_file_paths(record):
    """Add the file paths found under merge_path."""
    merge_path = Path(str(record.merge_path))
    logger.debug('searching: %s', merge_path)
def write_annotated_workbook(output_file, data):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "smpls"
    header = REQUIRED_INPUT_COLUMN_NAMES + ADDITIONAL_OUTPUT_COLUMN_NAMES
    ws.append(header)
    for record in data:
        row = [getattr(record, name) for name in header]
        ws.append(row)
    # bold = openpyxl.styles.Font(bold=True)
    # for c in ws.rows[0]:
    #     c.font = bold
    # TODO: Investigate setting column widths.
    wb.save(output_file)
    # get SNP paths
    snp_hits = sum(
            (list(merge_path.glob(pat)) for pat in SNP_PATTERNS), []
    )
    if len(snp_hits) != 1:
        logger.error(
             "{} number of snp_hits: {}".format(merge_path, len(snp_hits))
             )
        record.snp_file = None
        record.snp_path = None
    else:
        variants_snp_path, = snp_hits
        assert variants_snp_path.name.endswith(
            SNP_EXT[0]
        ) or variants_snp_path.name.endswith(SNP_EXT[1])
        record.snp_file = variants_snp_path.name
        record.snp_path = variants_snp_path
    # get INDEL paths
    indel_hits = sum(
            (list(merge_path.glob(pat)) for pat in INDEL_PATTERNS), []
    )
    if len(indel_hits) != 1:
        logger.error(
            "{} number of indel_hits: {}".format(merge_path, len(indel_hits))
        )
        record.indel_file = None
        record.indel_path = None
    else:
        variants_indel_path, = indel_hits
        assert variants_indel_path.name.endswith(
            INDEL_EXT[0]
        ) or variants_indel_path.name.endswith(INDEL_EXT[1])
        record.indel_file = variants_indel_path.name
        record.indel_path = variants_indel_path




class Generic:
    """Nothing special. Just a class to create objects with __dict__."""
    pass


if __name__ == '__main__':
    main()
