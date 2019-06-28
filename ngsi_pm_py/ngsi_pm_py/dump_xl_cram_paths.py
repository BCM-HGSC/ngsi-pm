#! /usr/bin/env python3

"""Outputs the cram paths of a workbook file."""

import argparse
import logging

import openpyxl

logger = logging.getLogger(__name__)

__version__ = "1.0.0"


def main():
    args = parse_args()
    config_logging(args.verbose)
    run(args.input_file)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", help="an XLSX workbook")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="increase output verbosity"
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s {}".format(__version__)
    )
    args = parser.parse_args()
    return args


def config_logging(verbose):
    global logger
    err_handler = logging.StreamHandler()
    level = logging.DEBUG if verbose else logging.INFO
    logger = logging.getLogger("dump_xl_cram_paths")
    logger.addHandler(err_handler)
    logger.setLevel(level)


def run(input_file):
    wb = openpyxl.load_workbook(input_file)
    sheet = wb["smpls"]
    active_sheet = wb.active
    assert sheet == active_sheet, (sheet.title, active_sheet.title)
    row_iter = iter(active_sheet.rows)
    header_row = next(row_iter)
    column_names = [c.value for c in header_row]
    records = [
        dict((k, v.value) for k, v in zip(column_names, row) if k in ("cram_path",))
        for row in row_iter
    ]
    for record in records:
        logger.info(record["cram_path"])


if __name__ == "__main__":
    main()
