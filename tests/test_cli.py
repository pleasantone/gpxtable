import argparse
import os
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import EXPECTED_DIR, expected_output, gpx_sample

# Define the paths
BASE_DIR = Path(__file__).resolve().parent.parent
CLI_SCRIPT_PATH = BASE_DIR / "src" / "gpxtable" / "cli.py"
DEFAULT_CONFIG_FILE = EXPECTED_DIR / "default-config.json"


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["TZ"] = "America/Los_Angeles"
    return subprocess.run(
        [sys.executable, str(CLI_SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


@pytest.fixture
def run_cli():
    return _run_cli


def test_cli_help(run_cli):
    result = run_cli(["--help"])
    assert result.returncode == 0
    assert "usage:" in result.stdout


def test_cli_invalid_file(run_cli):
    result = run_cli(["non_existent_file.gpx"])
    assert result.returncode != 0
    assert "Errno" in result.stderr


file_test_cases = [
    ("basecamp", ["--depart", "07/30/2023 09:15:00"]),
    ("basecamp-route", []),
    ("basecamp-tracks", ["--depart", "07/30/2022 09:15:00"]),
    ("scenic2", ["--depart", "07/30/2023 09:15:00"]),
    ("ich-north-fixed", ["--depart", "07/30/2023 09:15:00"]),
]


def input_output_names(filename: str) -> tuple[str, str]:
    return str(gpx_sample(filename)), str(expected_output(filename))


@pytest.mark.parametrize(("test_case", "arguments"), file_test_cases)
def test_cli_files_parm(run_cli, test_case: str, arguments: list):
    input_file, expected_file = input_output_names(test_case)
    args = [*arguments, input_file]
    result = run_cli(args)
    assert result.returncode == 0
    with open(expected_file) as f:
        expected = f.read()
    assert result.stdout == expected


def test_bad_xml(run_cli) -> None:
    input_file, _ = input_output_names("bad-xml")
    result = run_cli([input_file])
    assert result.returncode != 0
    assert "Error parsing XML" in result.stderr


def test_cli_invalid_departure(run_cli) -> None:
    input_file, _ = input_output_names("basecamp-route")
    result = run_cli(["--depart", "notadate", input_file])
    assert result.returncode != 0
    assert "invalid" in result.stderr.lower()


def test_cli_invalid_timezone(run_cli) -> None:
    input_file, _ = input_output_names("basecamp-route")
    result = run_cli(["--timezone", "Fake/Zone", input_file])
    assert result.returncode != 0
    assert "invalid timezone" in result.stderr.lower()


def test_dump_config_matches_sample(run_cli) -> None:
    """samples/default-config.json is included in the docs — keep it current."""
    result = run_cli(["--dump-config"])
    assert result.returncode == 0
    assert result.stdout == DEFAULT_CONFIG_FILE.read_text()


def generate_sample_output() -> None:
    for test_case, arguments in file_test_cases:
        input_file, output_file = input_output_names(test_case)
        args = [*arguments, input_file]
        print(f"gpxtable {' '.join(args)} > {output_file}...")
        result = _run_cli(args)
        assert result.returncode == 0
        with open(output_file, "w") as f:
            f.write(result.stdout)

    print(f"gpxtable --dump-config > {DEFAULT_CONFIG_FILE}...")
    result = _run_cli(["--dump-config"])
    assert result.returncode == 0
    DEFAULT_CONFIG_FILE.write_text(result.stdout)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generate", action="store_true", help="generate expected output files"
    )
    try:
        args = parser.parse_args()
    except ValueError as err:
        raise SystemExit(err) from err

    if args.generate:
        generate_sample_output()
    else:
        pytest.main()
