from openpyxl import Workbook
from pathlib import Path
from subprocess import run, DEVNULL, PIPE
import sys

import pytest


SCRIPT_PATH = 'bin/mplx_qc.py'
RESOURCE_BASE = Path('tests/mplx_qc/resources')


def test_ec0(tmpdir):
    cp = run_qc(tmpdir, 'tsv_main/ec_0.xlsx.tsv')
    check_results(cp, 0, 0, None, None)


def test_ec2(tmpdir):
    cp = run_qc(tmpdir, 'tsv_jwatt/ec_2_b.xlsx.tsv')
    check_results(cp, 2, 3,
                  'ERROR:mplx_qc:CRAM and JSON '
                  'have mismatching sets of barcodes.',
                  'tests/mplx_qc/resources/tsv_jwatt/ec_2_expect.tsv')


@pytest.mark.skip(reason="no way of currently testing this")
def test_ec3(tmpdir):
    """Note thot the JSON schema means that any attempt to use the same barcode
    twice in a JSON file will result in having one less sequencing event. This
    is because barcode is a dictionary key. Thus generating error code 2 is
    impossible."""
    cp = run_qc(tmpdir, 'tsv_jwatt/ec_3_b.xlsx.tsv')
    check_results(cp, 3, 3,
                  'ERROR:mplx_qc:Duplicate barcodes in JSON.',
                  'tests/mplx_qc/resources/tsv_jwatt/ec_3_expect.tsv')


def test_ec4(tmpdir):
    cp = run_qc(tmpdir, 'tsv_main/ec_4.xlsx.tsv')
    check_results(cp, 4, 1,
                  'ERROR:mplx_qc:Duplicate barcodes in CRAM.',
                  'tests/mplx_qc/resources/tsv_main/ec_4_expect.tsv')


def test_ec5(tmpdir):
    cp = run_qc(tmpdir, 'tsv_jwatt/ec_5_b.xlsx.tsv')
    check_results(cp, 5, 3,
                  'ERROR:mplx_qc:CRAM and JSON have different sample names.',
                  'tests/mplx_qc/resources/tsv_jwatt/ec_5_expect.tsv')


def test_ec6(tmpdir):
    cp = run_qc(tmpdir, 'tsv_main/ec_6.xlsx.tsv')
    check_results(cp, 6, 1,
                  'ERROR:mplx_qc:CRAM has wrong sample name.',
                  'tests/mplx_qc/resources/tsv_main/ec_6_expect.tsv')


def test_ec7(tmpdir):
    cp = run_qc(tmpdir, 'tsv_main/ec_7.xlsx.tsv')
    check_results(cp, 7, 1,
                  'ERROR:mplx_qc:CRAM contains multiple values for sample.',
                  'tests/mplx_qc/resources/tsv_main/ec_7_expect.tsv')


def check_results(cp, returncode, num_errs, error_prefix, expected_out_path):
    """Given a completed process, check the return code, the standard output
    against the contents of the file at expected_out_path, and the standard
    error agains a prefix that should appear at the start of every line and
    the expected number of lines."""
    assert bool(num_errs) == bool(error_prefix), 'bad test code'
    assert cp.returncode == returncode
    error_lines = cp.stderr.splitlines()
    assert len(error_lines) == num_errs
    for l in error_lines:
        assert l.startswith(error_prefix)
    if expected_out_path:
        assert cp.stdout == Path(expected_out_path).read_text()
    else:
        assert not cp.stdout


def run_qc(tmpdir, input_path):
    """Sets up all the paths, and then runs mplx_qc, returning the
    completed process object."""
    xlsx_path = str(tmpdir.join('test.xlsx'))
    print(xlsx_path)
    convert_tsv(RESOURCE_BASE/input_path, xlsx_path)
    args = [SCRIPT_PATH, xlsx_path]
    cp = run(args, stdin=DEVNULL, stdout=PIPE, stderr=PIPE,
             universal_newlines=True, timeout=10)
    print(cp.stdout)
    print(cp.stderr, file=sys.stderr)
    return cp


def convert_tsv(tsv_path, dst_path):
    wb = Workbook()
    ws = wb.active
    ws.title = 'smpls'
    with open(tsv_path) as fin:
        for line in fin.readlines():
            ws.append(line.rstrip().split('\t'))
    wb.save(dst_path)
