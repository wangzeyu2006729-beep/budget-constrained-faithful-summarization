#!/usr/bin/env bash
set -euo pipefail

ROOT=/path/to/NLP_generatesummary
PYTHON="$ROOT/.venv/bin/python"

exec "$PYTHON" "$ROOT/scripts/run_tri_metric_grid.py" "$@"
