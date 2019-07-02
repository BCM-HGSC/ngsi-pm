#! /usr/bin/env python3

"""Outputs the barcodes of a workbook file."""

import argparse
import logging

import openpyxl

from .version import __version__

logger = logging.getLogger(__name__)


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
    level = logging.DEBUG if verbose else logging.INFO
    err_handler = logging.StreamHandler()
    logger = logging.getLogger("dump_xl_barcodes")
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
        dict(
            (k, v.value)
            for k, v in zip(column_names, row)
            if k in ("lane_barcode", "sample_id_nwd_id")
        )
        for row in row_iter
    ]
    for record in records:
        logger.info(f"{record['lane_barcode']} \t {record['sample_id_nwd_id']}")


if __name__ == "__main__":
    main()
