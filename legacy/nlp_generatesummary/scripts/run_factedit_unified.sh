#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=/path/to/NLP_generatesummary
exec "$REPO_ROOT/papers/复现baseline/FACTEDIT/run_unified.sh" "$@"
