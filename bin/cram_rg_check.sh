#! /usr/bin/env bash

workbook="$1"

BIN_DIR=~/bin


"$BIN_DIR"/dump_xl_cram_paths.py "$workbook" 2>&1 |
    tr \\n \\0 |
    xargs -0 -n1 samtools view -H |
    "$BIN_DIR"/dump_rgs.py |
    diff - <("$BIN_DIR"/dump_xl_barcodes.py "$workbook" 2>&1)