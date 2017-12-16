from openpyxl import Workbook
from subprocess import run, DEVNULL, PIPE


SCRIPT_PATH = 'bin/mplx_qc.py'


def test_first_xlsx(tmpdir):
    xlsx_path = str(tmpdir.join('test.xlsx'))
    print(xlsx_path)
    convert_tsv('tests/mplx_qc/resources/tsv_jwatt/batchee_mplx_b.xlsx.tsv',
                xlsx_path)
    args = [SCRIPT_PATH, xlsx_path]
    cp = run(args, stdin=DEVNULL)  # , stdout=PIPE, stderr=PIPE, timeout=2)
    assert cp.returncode == 0


def convert_tsv(tsv_path, dst_path):
    wb = Workbook()
    ws = wb.active
    ws.title = 'smpls'
    with open(tsv_path) as fin:
        for line in fin.readlines():
            ws.append(line.rstrip().split('\t'))
    wb.save(dst_path)
