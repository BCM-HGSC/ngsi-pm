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
import os
from pathlib import Path
import sys
from subprocess import run, DEVNULL, PIPE

# after a blank line, import third-party libraries.
import openpyxl
from openpyxl.styles import Font

# After another blank line, import local libraries.
from dump_js_barcodes import Merge


def main():
    args = parse_args()
    run(args)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_file',
                        nargs='?',
                        type=argparse.FileType('rb'),
                        default=sys.stdin)
    # parser.add_argument('--add-arg2', '-a', action='store_true')
    args = parser.parse_args()
    return args


def tracefunc(frame, event, arg):
    """Set the system tracing function."""
    print(frame.f_lineno, event)
    return tracefunc


def run(args):
    input_file = args.input_file
    read_input(input_file)


def process_json_stream(json_paths):
    """from dump_js_barcodes.py import Merge,
    and parse JSON merge barcodes and JSON merge samples"""
    pass


def process_cram(cram_paths):
    """Read cram_paths, run samtools to parse
    CRAM barcodes and CRAM samples"""
    pass


def compare_barcodes(json_barcodes, cram_barcodes):
    """Compare the set of JSON barcodes and samples to
    the set of CRAM barcodes and samples"""
    pass


def read_input(input_file):
    """Read master XLSX of merged CRAMs and return list of objects containing
    the file paths."""
    wb = openpyxl.load_workbook(filename=input_file)
    sheet = wb.get_sheet_by_name('smpls')
    active_sheet = wb.active
    assert sheet == active_sheet, (sheet.title, active_sheet.title)
    row_iter = iter(active_sheet.rows)
    header_row = next(row_iter)
    column_names = [c.value for c in header_row]
    merged_crams = []
    for row in row_iter:
        merged_cram = Generic()
        for column_name, cell in zip(column_names, row):
            if column_name in ['json_path', 'cram_path']:
                value = cell.value
                setattr(merged_cram, column_name, value)
        merged_crams.append(merged_cram)
    return merged_crams
    # print(json_paths, cram_paths, sep='\t')
    # sys.exit()


class Generic:
    """To create objects with __dict__."""
    pass

# sys.settrace(tracefunc)
# input_file = 'AFIB_batch13_mplx.xlsx'
# read_input(input_file)


if __name__ == '__main__':
    main()
