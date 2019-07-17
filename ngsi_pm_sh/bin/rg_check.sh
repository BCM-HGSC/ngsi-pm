#! /usr/bin/env bash

workbook="$1"

dump_xl_bam_paths "$workbook" 2>&1 |
    tr \\n \\0 |
    xargs -0 -n1 samtools view -H |
    dump_rgs |
    diff - <(dump_xl_barcodes "$workbook" 2>&1 )
