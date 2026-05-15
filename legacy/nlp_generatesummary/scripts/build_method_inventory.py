from __future__ import annotations

import argparse
import json
from pathlib import Path

from unified_eval_common import build_markdown_table, choose_primary_fact_metric, discover_methods, ensure_output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a repository-wide method inventory.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory where inventory artifacts will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = ensure_output_dir(args.output_dir)
    methods = discover_methods()
    primary_fact = choose_primary_fact_metric()

    rows = []
    for entry in methods:
        rows.append(
            {
                "method_name": entry["method_id"],
                "method_type": entry.get("method_type", ""),
                "paper/source": entry.get("paper_source", ""),
                "status": entry.get("status", ""),
                "current_samples": entry.get("current_samples", ""),
                "entrypoint_or_dir": entry.get("entrypoint") or entry.get("source_dir") or "",
                "missing_prerequisites": "; ".join(entry.get("missing_prerequisites", [])),
                "notes": entry.get("notes", ""),
            }
        )

    json_path = output_dir / "method_inventory.json"
    md_path = output_dir / "method_inventory.md"

    json_path.write_text(
        json.dumps({"primary_fact_metric": primary_fact, "methods": methods}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    md_text = "\n".join(
        [
            "# Method Inventory",
            "",
            f"Primary FACT metric candidate: **{primary_fact['name']}**",
            "",
            build_markdown_table(
                rows,
                [
                    ("method_name", "method_name"),
                    ("method_type", "method_type"),
                    ("paper/source", "paper/source"),
                    ("status", "status"),
                    ("current_samples", "current_samples"),
                    ("entrypoint_or_dir", "entrypoint_or_dir"),
                    ("missing_prerequisites", "missing_prerequisites"),
                    ("notes", "notes"),
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
