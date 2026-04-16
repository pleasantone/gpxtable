.PHONY: help install install-dev test test-unit test-cli lint typecheck \
        generate-samples run-web run-web-gunicorn \
        demo-route demo-tracks demo-basecamp demo-config \
        build clean

# Default target
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Setup"
	@echo "  install        Install package (core deps only)"
	@echo "  install-dev    Install package with all extras (dev = gunicorn + tests + lint)"
	@echo ""
	@echo "Testing"
	@echo "  test           Run all tests"
	@echo "  test-unit      Run unit tests only (test_gpxtable.py)"
	@echo "  test-cli       Run CLI golden-file tests only"
	@echo "  generate-samples  Regenerate expected CLI output files in samples/"
	@echo ""
	@echo "Linting"
	@echo "  lint           Run ruff linter"
	@echo "  typecheck      Run mypy"
	@echo ""
	@echo "CLI demos"
	@echo "  demo-route     Run on Basecamp route sample"
	@echo "  demo-tracks    Run on Basecamp tracks sample (with departure time)"
	@echo "  demo-basecamp  Run on Basecamp combined sample"
	@echo "  demo-config    Dump default waypoint classifier config"
	@echo "  demo-custom    Run with custom config on route sample"
	@echo ""
	@echo "Web server"
	@echo "  run-web        Run Flask dev server"
	@echo "  run-gunicorn   Run gunicorn production server"
	@echo ""
	@echo "Build"
	@echo "  build          Build distribution packages"
	@echo "  clean          Remove build artifacts and caches"

# ── Setup ────────────────────────────────────────────────────────────────────

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# ── Testing ──────────────────────────────────────────────────────────────────

test:
	TZ=America/Los_Angeles pytest

test-unit:
	TZ=America/Los_Angeles pytest tests/test_gpxtable.py

test-cli:
	TZ=America/Los_Angeles pytest tests/test_cli.py

generate-samples:
	TZ=America/Los_Angeles python tests/test_cli.py --generate

# ── Linting ──────────────────────────────────────────────────────────────────

lint:
	ruff check .

typecheck:
	mypy src/

# ── CLI demos ────────────────────────────────────────────────────────────────

demo-route:
	gpxtable samples/basecamp-route.gpx

demo-tracks:
	gpxtable --departure "07/30/2023 09:15:00" samples/basecamp-tracks.gpx

demo-basecamp:
	gpxtable samples/basecamp.gpx

demo-config:
	gpxtable --dump-config

demo-custom: /tmp/myconfig.json
	gpxtable --config /tmp/myconfig.json samples/basecamp-route.gpx

/tmp/myconfig.json:
	gpxtable --dump-config > /tmp/myconfig.json

# ── Web server ───────────────────────────────────────────────────────────────

run-web:
	flask --app gpxtable.wsgi:create_app run

run-gunicorn:
	gunicorn "gpxtable.wsgi:create_app()"

# ── Build ────────────────────────────────────────────────────────────────────

build:
	python -m build

clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
