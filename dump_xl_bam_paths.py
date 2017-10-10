#! /usr/bin/env python3

import sys

import openpyxl


wb = openpyxl.load_workbook(sys.argv[1])
sheet = wb.get_sheet_by_name('smpls')
active_sheet = wb.active
assert sheet == active_sheet, (sheet.title, active_sheet.title)
row_iter = iter(active_sheet.rows)
header_row = next(row_iter)
column_names = [c.value for c in header_row]
records = [
    dict((k, v.value) for k, v in zip(column_names, row) if k in ('bam_path',))
    for row in row_iter
]
for record in records:
    print(record['bam_path'], sep='\t')
