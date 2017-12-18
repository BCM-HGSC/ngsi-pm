from openpyxl import Workbook
from pathlib import Path
from subprocess import run, DEVNULL, PIPE


SCRIPT_PATH = 'bin/mplx_qc.py'
RESOURCE_BASE = Path('tests/mplx_qc/resources')


# TODO: Check against sample provided by worklist.
# TODO: Check stdout and stderr.
# TODO: Check error codes 2 - 5.


def test_first_xlsx(tmpdir):
    cp = run_qc(tmpdir, 'tsv_jwatt/batchee_mplx_b.xlsx.tsv')
    assert cp.returncode == 0


def test_ec1(tmpdir):
    cp = run_qc(tmpdir, 'tsv_jwatt/ec_1_b.xlsx.tsv')
    assert cp.returncode == 1


def run_qc(tmpdir, input_path):
    """Sets up all the paths, and then runs mplx_qc, returning the
    completed process object."""
    xlsx_path = str(tmpdir.join('test.xlsx'))
    print(xlsx_path)
    convert_tsv(RESOURCE_BASE/input_path, xlsx_path)
    args = [SCRIPT_PATH, xlsx_path]
    cp = run(args, stdin=DEVNULL)  # , stdout=PIPE, stderr=PIPE, timeout=2)
    return cp


def convert_tsv(tsv_path, dst_path):
    wb = Workbook()
    ws = wb.active
    ws.title = 'smpls'
    with open(tsv_path) as fin:
        for line in fin.readlines():
            ws.append(line.rstrip().split('\t'))
    wb.save(dst_path)
