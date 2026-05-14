#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON="${PYTHON:-python3}"

echo "[validate] bash syntax"
find "$ROOT/scripts" "$ROOT/src" -type f -name '*.sh' -print0 |
  while IFS= read -r -d '' script; do
    bash -n "$script"
  done

echo "[validate] python AST parse without bytecode writes"
PYTHONDONTWRITEBYTECODE=1 "$PYTHON" - "$ROOT" <<'PY'
import ast
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
errors = []
files = []
for path in root.rglob("*.py"):
    if "__pycache__" in path.parts:
        continue
    files.append(path)
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except Exception as exc:
        errors.append((path, exc))

print(f"[validate] parsed_files={len(files)} errors={len(errors)}")
for path, exc in errors:
    print(f"{path}: {exc!r}", file=sys.stderr)
if errors:
    raise SystemExit(1)
PY

echo "[validate] runner --help imports"
for runner in \
  "$ROOT/src/bart/run.py" \
  "$ROOT/src/primera_multinews/run.py" \
  "$ROOT/src/llama3_8b/run.py" \
  "$ROOT/src/qwen3_5_9b/run.py" \
  "$ROOT/src/gemma4_e4b/run.py"
do
  PYTHONDONTWRITEBYTECODE=1 "$PYTHON" "$runner" --help >/dev/null
  echo "[validate] ok $runner --help"
done

echo "[validate] complete"
