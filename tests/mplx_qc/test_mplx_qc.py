from openpyxl import Workbook
from pathlib import Path
from subprocess import run, DEVNULL, PIPE
import sys

import pytest


SCRIPT_PATH = 'bin/mplx_qc.py'
RESOURCE_BASE = Path('tests/mplx_qc/resources')


# TODO: Check against sample provided by worklist.
# TODO: Check error codes 3 & 5.


def test_first_xlsx(tmpdir):
    cp = run_qc(tmpdir, 'tsv_jwatt/batchee_mplx_b.xlsx.tsv')
    assert cp.returncode == 0
    assert not cp.stdout
    assert not cp.stderr


def test_ec1(tmpdir):
    cp = run_qc(tmpdir, 'tsv_jwatt/ec_1_b.xlsx.tsv')
    assert cp.returncode == 1
    expect_path = Path('tests/mplx_qc/resources/tsv_jwatt/ec_1_expect.tsv')
    assert cp.stdout == expect_path.read_text()
    error_lines = cp.stderr.splitlines()
    for l in error_lines:
        assert l.startswith('ERROR:mplx_qc:CRAM and JSON '
                            'have mismatching sets of barcodes.')
    assert len(error_lines) == 3


@pytest.mark.skip(reason="no way of currently testing this")
def test_ec2(tmpdir):
    """Note thot the JSON schema means that any attempt to use the same barcode
    twice in a JSON file will result in having one less sequencing event. This
    is because barcode is a dictionary key. Thus generating error code 2 is
    impossible."""
    cp = run_qc(tmpdir, 'tsv_jwatt/ec_2_b.xlsx.tsv')
    assert cp.returncode == 2
    expect_path = Path('tests/mplx_qc/resources/tsv_jwatt/ec_2_expect.tsv')
    assert cp.stdout == expect_path.read_text()
    error_lines = cp.stderr.splitlines()
    for l in error_lines:
        assert l.startswith('ERROR:mplx_qc:Duplicate barcodes in JSON.')
    assert len(error_lines) == 3


def test_ec4(tmpdir):  # TODO: DRY out this code.
    cp = run_qc(tmpdir, 'tsv_jwatt/ec_4_b.xlsx.tsv')
    assert cp.returncode == 4
    expect_path = Path('tests/mplx_qc/resources/tsv_jwatt/ec_4_expect.tsv')
    assert cp.stdout == expect_path.read_text()
    error_lines = cp.stderr.splitlines()
    for l in error_lines:
        assert l.startswith('ERROR:mplx_qc:CRAM and JSON '
                            'have different sample names.')
    assert len(error_lines) == 3


def run_qc(tmpdir, input_path):
    """Sets up all the paths, and then runs mplx_qc, returning the
    completed process object."""
    xlsx_path = str(tmpdir.join('test.xlsx'))
    print(xlsx_path)
    convert_tsv(RESOURCE_BASE/input_path, xlsx_path)
    args = [SCRIPT_PATH, xlsx_path]
    cp = run(args, stdin=DEVNULL, stdout=PIPE, stderr=PIPE,
             universal_newlines=True, timeout=2)
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
