# samples

Expected output fixtures, versioned in this repository:

- `*.txt` — golden CLI output used by the `tests/test_cli.py` comparison tests.
  Regenerate with `make generate-samples` after an intentional output change.
- `default-config.json` — the default waypoint classifier, included in the docs.

The GPX **inputs** that produce these outputs are not here. They live in the
[`gpxsamples`](https://github.com/pleasantone/gpxsamples) submodule, checked out
at `gpxsamples/` in the repository root:

```bash
git submodule update --init   # or: make submodules
```
