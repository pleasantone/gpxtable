"""Shared paths and helpers for the gpxtable test suite.

Sample data is split across two locations:

* ``gpxsamples/`` — a git submodule holding the (large) ``.gpx`` inputs.
* ``samples/`` — the small expected-output fixtures versioned in this repo.
"""

from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent

#: GPX inputs, provided by the ``gpxsamples`` submodule.
GPX_DIR = BASE_DIR / "gpxsamples"

#: Expected CLI output and config fixtures, versioned in this repository.
EXPECTED_DIR = BASE_DIR / "samples"


def gpx_sample(name: str) -> Path:
    """Path to a ``.gpx`` input file in the samples submodule."""
    return GPX_DIR / f"{name}.gpx"


def expected_output(name: str) -> Path:
    """Path to the golden ``.txt`` output for a sample."""
    return EXPECTED_DIR / f"{name}.txt"


def pytest_configure(config: pytest.Config) -> None:
    """Fail fast with an actionable message if the submodule is not checked out."""
    if not any(GPX_DIR.glob("*.gpx")):
        raise pytest.UsageError(
            f"No GPX sample data found in {GPX_DIR}. "
            "Run 'git submodule update --init' to populate the gpxsamples submodule."
        )
