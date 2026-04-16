# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GPXtable converts GPX files (routes and tracks with waypoints) into Markdown or HTML tables useful for trip planning — primarily for motorcyclists who need to know fuel range, meal stops, and ETA at each waypoint. It handles both routes (point-to-point sequences) and tracks (recorded paths with associated waypoints that must be spatially matched to the track).

## Commands

```bash
# Install for development (includes web/gunicorn extras)
pip install -e ".[gunicorn,tests]"

# Run all tests
pytest

# Run a single test file
pytest tests/test_cli.py

# Run a single test by name
pytest tests/test_gpxtable.py::test_print_header

# Regenerate expected CLI output files in samples/
python tests/test_cli.py --generate

# Lint
flake8 .
ruff check .

# Run the CLI
gpxtable samples/basecamp-route.gpx
gpxtable --departure "07/30/2023 09:15:00" samples/basecamp-tracks.gpx

# Dump/customize waypoint classifier config
gpxtable --dump-config > myconfig.json
gpxtable --config myconfig.json samples/basecamp-route.gpx

# Run the Flask dev server
flask --app gpxtable.wsgi:create_app run
```

## Architecture

The package has four modules under `src/gpxtable/`:

- **`gpxtable.py`** — Core library. Contains `GPXTableCalculator` (the main class), plus extension classes `GPXTrackExt`, `GPXWaypointExt`, `GPXRoutePointExt`, and `GPXPointMixin`. All distance calculations are in meters internally; conversion to miles/km happens only at display time. Speed is always stored internally in km/h.

- **`cli.py`** — Thin CLI wrapper around `GPXTableCalculator`. Handles argument parsing, optional HTML conversion via `markdown2`, and JSON config loading. The `--departure` flag uses `_DateParser` for natural-language date parsing.

- **`wsgi.py`** — Flask Blueprint (`bp`) + `create_app()` factory for web deployment (Google App Engine). Accepts GPX uploads or URLs. `create_table()` is the WSGI-facing equivalent of `cli.create_markdown()`, with an `output_format` parameter supporting `"html"`, `"markdown"`, and `"htmlcode"`.

- **`__init__.py`** — Exports `GPXTableCalculator` and `GPXTABLE_DEFAULT_WAYPOINT_CLASSIFIER` only.

### Key design patterns

**Waypoint classification** (`GPXTABLE_DEFAULT_WAYPOINT_CLASSIFIER`): A JSON-configurable list of dicts that maps GPX symbol names or waypoint name regexes to stop behavior (delay in minutes, fuel reset, display marker like `G`/`L`/`GL`). The list is matched in order; first match wins. This is the primary extension point — users can override it with `--config`.

**Route vs. Track handling**: Routes are sequential point sequences with explicit geometry (and Garmin extension data for shape points and stop durations). Tracks are GPS recordings; waypoints must be spatially located on the track using `GPXTrackExt.get_nearest_locations()`, which uses a threshold of 0.1% of total track distance and deduplicates within 10 km to handle looping routes.

**Mixin inheritance**: `GPXPointMixin` uses cooperative multiple inheritance to extend `gpxpy`'s `GPXWaypoint` and `GPXRoutePoint` without modifying them. `GPXRoutePointExt.delay()` overrides the mixin's default to read Garmin TripExtensions XML (`trp:StopDuration`). The `shaping_point()` method filters out Garmin via/shape points that shouldn't appear in the output table.

**Garmin XML extensions**: Two namespaces are parsed — `trp:` (TripExtensions/v1) for stop durations and departure times, and `gpxx:` (GpxExtensions/v3) for route shape points (`gpxx:rpt`) used in distance calculations.

**Fuel tracking**: `last_gas` accumulates distance since the last fuel stop. The distance column shows `since_gas/total` for fuel stops and the final waypoint, and just `total` for others.

### Testing approach

CLI tests in `test_cli.py` use golden-file comparison: they run the CLI subprocess and diff against `samples/*.txt` files. When changing output format, regenerate these with `python tests/test_cli.py --generate`. The test environment sets `TZ=America/Los_Angeles` for reproducibility.

Unit tests construct `GPX` objects directly (no file I/O) and assert on `StringIO` output or return values.

## Deployment

Deploys to Google App Engine on push to `main` via `.github/workflows/python-app.yml`. The `SECRET_KEY` for Flask sessions comes from `SECRET_KEY` environment variable or a random token per startup. Max upload size is 16 MB.
