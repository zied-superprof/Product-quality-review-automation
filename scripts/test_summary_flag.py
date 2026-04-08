#!/usr/bin/env python3
"""
TDD test for --summary flag in structural_validator.py (TOK-02).

RED phase: These tests verify expected behavior before implementation.
Run with: python3 scripts/test_summary_flag.py
"""

import ast
import subprocess
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
VALIDATOR = PROJECT_ROOT / 'scripts' / 'structural_validator.py'
SAMPLE_CSV = PROJECT_ROOT / 'samples' / 'relance_3.csv'


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATOR)] + args,
        capture_output=True,
        text=True,
    )


def test_summary_flag_in_help():
    """Test 1: --summary appears in --help output."""
    result = run(['--help'])
    assert '--summary' in result.stdout, (
        f"FAIL test_summary_flag_in_help: '--summary' not in --help output.\n"
        f"stdout: {result.stdout[:500]}"
    )
    print('PASS test_summary_flag_in_help')


def test_summary_flag_prints_table(tmp_path):
    """Test 2: --summary prints a compact table with expected headers."""
    result = run(['--input', str(SAMPLE_CSV), '--summary'])
    assert result.returncode == 0, f"FAIL: exit code {result.returncode}\nstderr: {result.stderr}"
    lines = result.stdout.strip().splitlines()
    assert len(lines) >= 3, f"FAIL: too few lines in output: {lines}"
    header = lines[0]
    assert 'Market' in header, f"FAIL: 'Market' not in header: {header!r}"
    assert 'Errors' in header, f"FAIL: 'Errors' not in header: {header!r}"
    assert 'Warnings' in header, f"FAIL: 'Warnings' not in header: {header!r}"
    assert 'Info' in header, f"FAIL: 'Info' not in header: {header!r}"
    # No JSON in output
    assert '{' not in result.stdout, "FAIL: JSON braces found in --summary output"
    print('PASS test_summary_flag_prints_table')


def test_summary_with_output_writes_json_and_prints_table(tmp_path):
    """Test 3: --summary + --output writes full JSON to file AND prints compact table to stdout."""
    out_file = tmp_path / 'test_out.json'
    result = run(['--input', str(SAMPLE_CSV), '--output', str(out_file), '--summary'])
    assert result.returncode == 0, f"FAIL: exit code {result.returncode}\nstderr: {result.stderr}"
    # JSON file written
    assert out_file.exists(), f"FAIL: output file not created at {out_file}"
    with open(out_file) as f:
        data = json.load(f)
    assert 'issues' in data, "FAIL: JSON missing 'issues' key"
    # Compact table printed to stdout
    assert 'Market' in result.stdout, f"FAIL: 'Market' not in stdout: {result.stdout[:200]}"
    print('PASS test_summary_with_output_writes_json_and_prints_table')


def test_no_regression_with_output_only(tmp_path):
    """Test 4: Without --summary, --output behavior is unchanged (stderr summary, no stdout)."""
    out_file = tmp_path / 'test_out2.json'
    result = run(['--input', str(SAMPLE_CSV), '--output', str(out_file)])
    assert result.returncode == 0, f"FAIL: exit code {result.returncode}\nstderr: {result.stderr}"
    assert out_file.exists(), "FAIL: output file not created"
    assert 'Structural validation complete' in result.stderr, (
        f"FAIL: stderr summary missing. stderr: {result.stderr[:200]}"
    )
    # stdout should be empty (nothing printed when --output given without --summary)
    assert result.stdout.strip() == '', (
        f"FAIL: unexpected stdout when using --output without --summary: {result.stdout[:200]}"
    )
    print('PASS test_no_regression_with_output_only')


def test_no_regression_no_flags():
    """Test 5: Without any flags, full JSON printed to stdout."""
    result = run(['--input', str(SAMPLE_CSV)])
    assert result.returncode == 0, f"FAIL: exit code {result.returncode}"
    parsed = json.loads(result.stdout)
    assert 'issues' in parsed, "FAIL: full JSON not printed to stdout"
    assert 'summary' in parsed, "FAIL: 'summary' key missing in JSON"
    print('PASS test_no_regression_no_flags')


def test_summary_has_total_row():
    """Test 6: Compact table includes a TOTAL row at the bottom."""
    result = run(['--input', str(SAMPLE_CSV), '--summary'])
    assert result.returncode == 0, f"FAIL: exit code {result.returncode}"
    assert 'TOTAL' in result.stdout, f"FAIL: 'TOTAL' row missing from output:\n{result.stdout}"
    print('PASS test_summary_has_total_row')


def test_file_parses_without_syntax_errors():
    """Test 7: structural_validator.py parses without syntax errors."""
    with open(VALIDATOR) as f:
        source = f.read()
    try:
        ast.parse(source)
        print('PASS test_file_parses_without_syntax_errors')
    except SyntaxError as e:
        print(f"FAIL test_file_parses_without_syntax_errors: {e}")
        sys.exit(1)


if __name__ == '__main__':
    import tempfile

    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        tests = [
            (test_summary_flag_in_help, []),
            (test_summary_flag_prints_table, [tmp_path]),
            (test_summary_with_output_writes_json_and_prints_table, [tmp_path]),
            (test_no_regression_with_output_only, [tmp_path]),
            (test_no_regression_no_flags, []),
            (test_summary_has_total_row, []),
            (test_file_parses_without_syntax_errors, []),
        ]
        for fn, args in tests:
            try:
                fn(*args)
            except AssertionError as e:
                print(str(e))
                failures.append(fn.__name__)
            except Exception as e:
                print(f"ERROR {fn.__name__}: {e}")
                failures.append(fn.__name__)

    if failures:
        print(f"\n{len(failures)} test(s) FAILED: {', '.join(failures)}")
        sys.exit(1)
    else:
        print(f"\nAll tests PASSED")
