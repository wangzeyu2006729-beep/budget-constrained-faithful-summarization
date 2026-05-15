from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from unified_eval_common import PAPERS_ROOT, ROOT, build_markdown_table, ensure_output_dir


SCRIPT_SUFFIXES = {".py", ".sh", ".ps1"}
WINDOWS_PATH_RE = re.compile(r"[A-Za-z]:\\")
EXCLUDED_PARTS = {".git", "__pycache__"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a server-side inventory of repo and paper baseline scripts.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory where inventory artifacts will be written.",
    )
    return parser.parse_args()


def iter_script_paths(root: Path) -> list[Path]:
    results: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in SCRIPT_SUFFIXES:
            continue
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        if any(part.startswith(".venv") for part in path.parts):
            continue
        results.append(path)
    return sorted(results)


def classify_kind(relative_path: Path) -> str:
    path_text = relative_path.as_posix()
    name = relative_path.name
    if ".ps1" in name or relative_path.suffix == ".ps1":
        return "windows_wrapper"
    if "/_legacy/" in f"/{path_text}/" or "/legacy/" in f"/{path_text}/":
        return "legacy"
    if "/tests/" in f"/{path_text}/" or name.startswith("test_"):
        return "test"
    if name.startswith("run") or name.startswith("train") or name.startswith("eval") or name.startswith("build_"):
        return "entrypoint"
    if relative_path.parts and relative_path.parts[0] == "scripts":
        return "entrypoint"
    return "support"


def classify_status(kind: str, has_windows_path: bool) -> str:
    if kind == "windows_wrapper":
        return "windows_only"
    if kind == "legacy":
        return "legacy"
    if has_windows_path:
        return "needs_server_cleanup"
    return "server_visible"


def build_record(scope: str, base_root: Path, path: Path) -> dict[str, object]:
    relative_path = path.relative_to(base_root)
    text = path.read_text(encoding="utf-8", errors="replace")
    kind = classify_kind(relative_path)
    has_windows_path = bool(WINDOWS_PATH_RE.search(text)) or "powershell" in text.lower()
    status = classify_status(kind, has_windows_path)
    top_group = relative_path.parts[0] if relative_path.parts else "."
    return {
        "scope": scope,
        "path": str(path),
        "relative_path": str(relative_path),
        "top_group": top_group,
        "suffix": path.suffix,
        "kind": kind,
        "status": status,
        "has_windows_path": has_windows_path,
    }


def main() -> None:
    args = parse_args()
    output_dir = ensure_output_dir(args.output_dir)

    records: list[dict[str, object]] = []
    for path in iter_script_paths(ROOT):
        records.append(build_record("repo", ROOT, path))
    if PAPERS_ROOT.exists():
        for path in iter_script_paths(PAPERS_ROOT):
            records.append(build_record("papers_baseline", PAPERS_ROOT, path))

    records.sort(key=lambda item: (str(item["scope"]), str(item["relative_path"])))

    summary = {
        "total_scripts": len(records),
        "by_scope": dict(Counter(str(item["scope"]) for item in records)),
        "by_status": dict(Counter(str(item["status"]) for item in records)),
        "by_kind": dict(Counter(str(item["kind"]) for item in records)),
    }

    json_path = output_dir / "server_script_inventory.json"
    md_path = output_dir / "server_script_inventory.md"
    json_path.write_text(
        json.dumps({"summary": summary, "scripts": records}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    md_rows = [
        {
            "scope": item["scope"],
            "path": item["relative_path"],
            "top_group": item["top_group"],
            "kind": item["kind"],
            "status": item["status"],
            "windows_path": "yes" if item["has_windows_path"] else "",
        }
        for item in records
    ]
    md_text = "\n".join(
        [
            "# Server Script Inventory",
            "",
            f"- Total scripts: {summary['total_scripts']}",
            f"- By scope: {summary['by_scope']}",
            f"- By status: {summary['by_status']}",
            f"- By kind: {summary['by_kind']}",
            "",
            build_markdown_table(
                md_rows,
                [
                    ("scope", "scope"),
                    ("path", "path"),
                    ("top_group", "top_group"),
                    ("kind", "kind"),
                    ("status", "status"),
                    ("windows_path", "windows_path"),
                ],
            ),
            "",
        ]
    )
    md_path.write_text(md_text, encoding="utf-8")

    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
