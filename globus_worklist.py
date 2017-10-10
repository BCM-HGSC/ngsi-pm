#!/usr/bin/env python3

"""To create Globus WORKLIST.
Read a master workbook and output an XLSX workbook.""" 

# First come standard libraries, in alphabetical order.
import argparse
import csv
import logging
import os
import pprint
import re
import sys
import warnings

# After a blank line, import third-party libraries.
import openpyxl

# After another blank line, import local libraries.

__version__ = '1.0.0-unstable'

logger = logging.getLogger(__name__)

# Column names
REQUIRED_INPUT_COLUMN_NAMES = '''
    lane_barcode
    hgsc_xfer_subdir
    batch
    sample_id_nwd_id
    run_name
    current_bam_name
    new_bam_name
    result_path
'''.split()  # The order of the columns in the output

REQUIRED_INPUT_COLUMN_NAMES_SET = set(REQUIRED_INPUT_COLUMN_NAMES)
ADDITIONAL_OUTPUT_COLUMN_NAMES = '''
    bam_path
'''.split()  # The order of the columns in the output

# Extensions, useful when there are many extensions
BAM_EXT = 'hgv.bam'


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
                        help='will default to MASTER_globus.xlsx')
    parser.add_argument('-v', '--verbose', action='store_true', 
                        help='increase output verbosity') 
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()
    if args.output_file is None:
        args.output_file = munge_input_file_name(args.input_file)
    return args


def munge_input_file_name(input_file_name):
    """X.xlsx ->X_globus.xlsx"""
    assert input_file_name.endswith('.xlsx')
    return input_file_name[:-5] + '_globus.xlsx'


def config_logging(args):
    global logger
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level)
    logger = logging.getLogger('globus_worklist')


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
        get_new_bam_name(record)
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
    # read header row and parse into column names
    column_names = [c.value for c in header_row]
    # fix bad names
    column_names = [n.replace('/', '_') for n in column_names]
    # column_names = re.sub(r\'[-"/\.$]', '_', column_names)
    logger.debug('columns: %s', column_names)
    missing = REQUIRED_INPUT_COLUMN_NAMES_SET - set(column_names)
    assert not missing, 'missing: {}'.format(sorted(missing))
    data = []
    for row in row_iter:
        record = Generic()
        for column_name, cell in zip(column_names, row):
            if column_name in REQUIRED_INPUT_COLUMN_NAMES_SET:
                value = cell.value
                setattr(record, column_name, value)
        if record.result_path and record.result_path[0] != '#':
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
    """Add the file paths found under result_path."""
    result_path = record.result_path
    logger.debug('searching: %s', result_path)
    for file_name in os.listdir(result_path):
        if file_name.endswith(BAM_EXT):
            record.current_bam_name = file_name
            record.bam_path = os.path.join(result_path, file_name)


def get_new_bam_name(record):
    """new_bam_name = sample_id_nwd_id + "-" + current_bam_name"""
    sample_id_nwd_id = record.sample_id_nwd_id
    logger.debug('searching: %s', sample_id_nwd_id)
    current_bam_name = record.current_bam_name
    logger.debug('searching: %s', current_bam_name)
    record.new_bam_name = sample_id_nwd_id + "-" + current_bam_name


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
    # wh: replace 'sample_id_nwd_id' back to 'sample_id/nwd_id' for wb.save
    wb.save(output_file)


class Generic:
    """Nothing special. Just a class to create objects with __dict__."""
    pass


if __name__ == '__main__':
    main()
