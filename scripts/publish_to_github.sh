#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

REPO_NAME="${REPO_NAME:-budget-constrained-and-faithful}"
VISIBILITY="${VISIBILITY:-private}"
REMOTE_NAME="${REMOTE_NAME:-origin}"
BRANCH="${BRANCH:-main}"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"

usage() {
  cat <<'EOF'
Usage:
  GH_TOKEN=... scripts/run_live.sh --name publish_github -- \
    bash scripts/publish_to_github.sh

Environment:
  GH_TOKEN or GITHUB_TOKEN  GitHub token with repo creation permission.
  REPO_NAME                Default: budget-constrained-and-faithful.
  VISIBILITY               private or public. Default: private.
  REMOTE_NAME              Default: origin.
  BRANCH                   Default: main.

The script creates a GitHub repository and pushes this release directory.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ "$VISIBILITY" != "private" ] && [ "$VISIBILITY" != "public" ]; then
  echo "VISIBILITY must be private or public." >&2
  exit 2
fi

if [ -z "$TOKEN" ]; then
  echo "Missing GH_TOKEN or GITHUB_TOKEN. Cannot create a GitHub repo without credentials." >&2
  usage >&2
  exit 2
fi

if ! git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$ROOT" init
fi

git -C "$ROOT" branch -M "$BRANCH"
git -C "$ROOT" add .

if ! git -C "$ROOT" diff --cached --quiet; then
  if ! git -C "$ROOT" config user.name >/dev/null || ! git -C "$ROOT" config user.email >/dev/null; then
    echo "Git user.name and user.email are not configured. Configure them before publishing." >&2
    echo "Example:" >&2
    echo "  git -C \"$ROOT\" config user.name \"Your Name\"" >&2
    echo "  git -C \"$ROOT\" config user.email \"you@example.com\"" >&2
    exit 2
  fi
  git -C "$ROOT" commit -m "Initial ACL reproducibility release"
fi

API_JSON="$(mktemp)"
HTTP_CODE="$(
  curl -sS -o "$API_JSON" -w "%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    https://api.github.com/user/repos \
    -d "{\"name\":\"$REPO_NAME\",\"private\":$([ "$VISIBILITY" = private ] && echo true || echo false),\"auto_init\":false}"
)"

if [ "$HTTP_CODE" != "201" ] && [ "$HTTP_CODE" != "422" ]; then
  echo "GitHub API failed with HTTP $HTTP_CODE:" >&2
  cat "$API_JSON" >&2
  rm -f "$API_JSON"
  exit 1
fi

CLONE_URL="$(python3 - "$API_JSON" <<'PY'
import json
import sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as handle:
    payload = json.load(handle)
print(payload.get("clone_url") or payload.get("html_url", "").replace("https://github.com/", "https://github.com/") + ".git")
PY
)"
HTML_URL="$(python3 - "$API_JSON" <<'PY'
import json
import sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as handle:
    payload = json.load(handle)
print(payload.get("html_url", ""))
PY
)"
rm -f "$API_JSON"

if [ -z "$CLONE_URL" ] || [ "$CLONE_URL" = ".git" ]; then
  echo "Could not determine GitHub clone URL." >&2
  exit 1
fi

AUTH_URL="${CLONE_URL/https:\\/\\//https:\/\/x-access-token:${TOKEN}@}"
if git -C "$ROOT" remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
  git -C "$ROOT" remote set-url "$REMOTE_NAME" "$CLONE_URL"
else
  git -C "$ROOT" remote add "$REMOTE_NAME" "$CLONE_URL"
fi

git -C "$ROOT" push "$AUTH_URL" "$BRANCH:$BRANCH"
git -C "$ROOT" remote set-url "$REMOTE_NAME" "$CLONE_URL"

echo "Published $VISIBILITY repository:"
echo "${HTML_URL:-$CLONE_URL}"
