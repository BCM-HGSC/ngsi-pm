from openpyxl import Workbook
from pathlib import Path
from subprocess import run, DEVNULL, PIPE
import sys

import pytest

from ngsi_pm_py import mplx_qc

current_path = Path(__file__).resolve()
RESOURCE_BASE = current_path.parent / "resources"


# Functional tests

def test_ec0(tmpdir):
    cp = run_mplx_qc_xlsx(tmpdir, 'tsv_main/ec_0.xlsx.tsv')
    check_output(cp, 0, 0, None, None)


def test_ec2(tmpdir):
    cp = run_mplx_qc_xlsx(tmpdir, 'tsv_jwatt/ec_2_b.xlsx.tsv')
    check_output(cp, 2, 3,
                 'ERROR:mplx_qc:CRAM and JSON '
                 'have mismatching sets of barcodes.',
                 RESOURCE_BASE/'tsv_jwatt/ec_2_expect.tsv')


@pytest.mark.skip(reason="no way of currently testing this")
def test_ec3(tmpdir):
    """Note thot the JSON schema means that any attempt to use the same barcode
    twice in a JSON file will result in having one less sequencing event. This
    is because barcode is a dictionary key. Thus generating error code 2 is
    impossible."""
    cp = run_mplx_qc_xlsx(tmpdir, 'tsv_jwatt/ec_3_b.xlsx.tsv')
    check_output(cp, 3, 3,
                 'ERROR:mplx_qc:Duplicate barcodes in JSON.',
                 RESOURCE_BASE/'tsv_jwatt/ec_3_expect.tsv')


def test_ec4(tmpdir):
    cp = run_mplx_qc_xlsx(tmpdir, 'tsv_main/ec_4.xlsx.tsv')
    check_output(cp, 4, 1,
                 'ERROR:mplx_qc:Duplicate barcodes in CRAM.',
                 RESOURCE_BASE/'tsv_main/ec_4_expect.tsv')


def test_ec5(tmpdir):
    cp = run_mplx_qc_xlsx(tmpdir, 'tsv_jwatt/ec_5_b.xlsx.tsv')
    check_output(cp, 5, 3,
                 'ERROR:mplx_qc:CRAM and JSON have different sample names.',
                 RESOURCE_BASE/'tsv_jwatt/ec_5_expect.tsv')


def test_ec6(tmpdir):
    cp = run_mplx_qc_xlsx(tmpdir, 'tsv_main/ec_6.xlsx.tsv')
    check_output(cp, 6, 1,
                 'ERROR:mplx_qc:CRAM has wrong sample name.',
                 RESOURCE_BASE/'tsv_main/ec_6_expect.tsv')


def test_ec7(tmpdir):
    cp = run_mplx_qc_xlsx(tmpdir, 'tsv_main/ec_7.xlsx.tsv')
    check_output(cp, 7, 1,
                 'ERROR:mplx_qc:CRAM contains multiple values for sample.',
                 RESOURCE_BASE/'tsv_main/ec_7_expect.tsv')


def test_ec0_tsv():
    cp = run_mplx_qc(RESOURCE_BASE/'tsv_main/ec_0.xlsx.tsv')
    check_output(cp, 0, 0, None, None)


def test_ec7_tsv():
    cp = run_mplx_qc(RESOURCE_BASE/'tsv_main/ec_7.xlsx.tsv')
    check_output(cp, 7, 1,
                 'ERROR:mplx_qc:CRAM contains multiple values for sample.',
                 RESOURCE_BASE/'tsv_main/ec_7_expect.tsv')


def run_mplx_qc_xlsx(tmpdir, input_path):
    """Sets up all the paths, and then runs mplx_qc, returning the
    completed process object."""
    xlsx_path = str(tmpdir.join('test.xlsx'))
    print(xlsx_path)
    convert_tsv(RESOURCE_BASE/input_path, xlsx_path)
    return run_mplx_qc(xlsx_path)


def convert_tsv(tsv_path, dst_path):
    wb = Workbook()
    ws = wb.active
    ws.title = 'smpls'
    with open(tsv_path) as fin:
        for line in fin.readlines():
            ws.append(line.rstrip().split('\t'))
    wb.save(dst_path)


def run_mplx_qc(input_path):
    """Runs mplx_qc, returning the completed process object."""
    args = ["mplx_qc", input_path]
    cp = run(args, stdin=DEVNULL, stdout=PIPE, stderr=PIPE,
             universal_newlines=True, timeout=20)
    print(cp.stdout)
    print(cp.stderr, file=sys.stderr)
    return cp


def check_output(cp, returncode, num_errs, error_prefix, expected_out_path):
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


# Unit tetss

def test_ec0_unit(capsys):
    error_code = mplx_qc.run_qc(str(RESOURCE_BASE/'tsv_main/ec_0.xlsx.tsv'))
    out, err = capsys.readouterr()
    print(out)
    print(err, file=sys.stderr)
    assert error_code == 0


def test_ec2_unit(capsys):
    error_code = mplx_qc.run_qc(str(RESOURCE_BASE/'tsv_jwatt/ec_2_b.xlsx.tsv'))
    assert error_code == 2
    check_run_qc(capsys, 3,
                 'CRAM and JSON have mismatching sets of barcodes.',
                 RESOURCE_BASE/'tsv_jwatt/ec_2_expect.tsv')


def test_ec4_unit(capsys):
    error_code = mplx_qc.run_qc(str(RESOURCE_BASE/'tsv_main/ec_4.xlsx.tsv'))
    assert error_code == 4
    check_run_qc(capsys, 1,
                 'Duplicate barcodes in CRAM.',
                 RESOURCE_BASE/'tsv_main/ec_4_expect.tsv')


def test_ec5_unit(capsys):
    error_code = mplx_qc.run_qc(str(RESOURCE_BASE/'tsv_jwatt/ec_5_b.xlsx.tsv'))
    assert error_code == 5
    check_run_qc(capsys, 3,
                 'CRAM and JSON have different sample names.',
                 RESOURCE_BASE/'tsv_jwatt/ec_5_expect.tsv')


def test_ec6_unit(capsys):
    error_code = mplx_qc.run_qc(str(RESOURCE_BASE/'tsv_main/ec_6.xlsx.tsv'))
    assert error_code == 6
    check_run_qc(capsys, 1,
                 'CRAM has wrong sample name.',
                 RESOURCE_BASE/'tsv_main/ec_6_expect.tsv')


def test_ec7_unit(capsys):
    error_code = mplx_qc.run_qc(str(RESOURCE_BASE/'tsv_main/ec_7.xlsx.tsv'))
    assert error_code == 7
    check_run_qc(capsys, 1,
                 'CRAM contains multiple values for sample.',
                 RESOURCE_BASE/'tsv_main/ec_7_expect.tsv')


def test_ec9_unit(capsys):
    """If an RG in a CRAM file is missing a PU..."""
    error_code = mplx_qc.run_qc(str(RESOURCE_BASE/'tsv_main/ec_9.tsv'))
    assert error_code == 9
    check_run_qc(capsys, 1,
                 'An RG in the CRAM is missing its PU:',
                 RESOURCE_BASE/'tsv_main/ec_9_expect.tsv')


def test_ec10_unit(capsys):
    """If an RG in a CRAM file is missing an SM..."""
    error_code = mplx_qc.run_qc(str(RESOURCE_BASE/'tsv_main/ec_10.tsv'))
    assert error_code == 10
    check_run_qc(capsys, 1,
                 'An RG in the CRAM is missing its SM:',
                 RESOURCE_BASE/'tsv_main/ec_10_expect.tsv')


def test_ec12_unit(capsys):
    """If a JSON file is too bad to read..."""
    error_code = mplx_qc.run_qc(str(RESOURCE_BASE/'tsv_main/ec_12.tsv'))
    assert error_code == 12
    check_run_qc(capsys, 1,
                 'JSON is bad:',
                 RESOURCE_BASE/'tsv_main/ec_12_expect.tsv')


def test_ec13_unit(capsys):
    """If a CRAM file is too bad to read..."""
    error_code = mplx_qc.run_qc(str(RESOURCE_BASE/'tsv_main/ec_13.tsv'))
    assert error_code == 13
    check_run_qc(capsys, 1,
                 'CRAM is bad:',
                 RESOURCE_BASE/'tsv_main/ec_13_expect.tsv')


def test_ec14_unit(capsys):
    """If a JSON is missing or not a file..."""
    error_code = mplx_qc.run_qc(str(RESOURCE_BASE/'tsv_main/ec_14.tsv'))
    assert error_code == 14
    check_run_qc(capsys, 1,
                 'JSON is missing:',
                 RESOURCE_BASE/'tsv_main/ec_14_expect.tsv')


def test_ec15_unit(capsys):
    """If a CRAM is missing or not a file..."""
    error_code = mplx_qc.run_qc(str(RESOURCE_BASE/'tsv_main/ec_15.tsv'))
    assert error_code == 15
    check_run_qc(capsys, 1,
                 'CRAM is missing:',
                 RESOURCE_BASE/'tsv_main/ec_15_expect.tsv')


def test_ec17_unit(capsys):
    """If the input worklist file has bad contents..."""
    error_code = mplx_qc.run_qc(str(RESOURCE_BASE/'tsv_main/ec_17.tsv'))
    assert error_code == 17
    check_run_qc(capsys, 1,
                 'Input file has bad contents:',
                 RESOURCE_BASE/'empty_file')


def test_ec17_xlsx_unit(capsys):
    """If the input worklist file has bad contents..."""
    error_code = mplx_qc.run_qc(str(RESOURCE_BASE/'bad.xlsx'))
    assert error_code == 17
    check_run_qc(capsys, 1,
                 'Input file has bad contents:',
                 RESOURCE_BASE/'empty_file')


def test_ec18_unit(capsys):
    """If the input worklist file has the wrong extension..."""
    error_code = mplx_qc.run_qc(str(RESOURCE_BASE/'foo.foo'))
    assert error_code == 18
    check_run_qc(capsys, 1,
                 'Input file has bad extension:',
                 RESOURCE_BASE/'empty_file')


def test_ec19_unit(capsys):
    """If the input worklist file isn't a file..."""
    error_code = mplx_qc.run_qc(str(RESOURCE_BASE))
    assert error_code == 19
    check_run_qc(capsys, 1,
                 'Input is not a file:',
                 RESOURCE_BASE/'empty_file')


def test_ec20_unit(capsys):
    """If the input worklist file doesn't even exist..."""
    error_code = mplx_qc.run_qc(str(RESOURCE_BASE/'foo.tsv'))
    assert error_code == 20
    check_run_qc(capsys, 1,
                 'Input file is missing:',
                 RESOURCE_BASE/'empty_file')


def test_ec20_xlsx_unit(capsys):
    """If the input worklist file doesn't even exist..."""
    error_code = mplx_qc.run_qc(str(RESOURCE_BASE/'foo.xlsx'))
    assert error_code == 20
    check_run_qc(capsys, 1,
                 'Input file is missing:',
                 RESOURCE_BASE/'empty_file')


def check_run_qc(capsys, num_errs, error_prefix, expected_out_path):
    out, err = capsys.readouterr()
    print(out)
    print(err, file=sys.stderr)
    error_lines = err.splitlines()
    assert len(error_lines) == num_errs
    for l in error_lines:
        assert l.startswith(error_prefix)
    assert out == Path(expected_out_path).read_text()
