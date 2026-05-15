from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from unified_eval_common import ROOT, build_command_for_method, choose_primary_fact_metric, discover_methods, ensure_output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build or execute a unified 500-sample evaluation plan.")
    parser.add_argument("--methods", nargs="*", default=[], help="Optional subset of method ids.")
    parser.add_argument("--sample-limit", type=int, default=500, help="Comparable sample limit (default: 500).")
    parser.add_argument("--execute", action="store_true", help="Execute commands instead of only writing a manifest.")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip methods that already have a result with at least sample-limit samples.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory where the manifest will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = ensure_output_dir(args.output_dir)
    methods = discover_methods()
    selected_ids = set(args.methods)
    if selected_ids:
        methods = [entry for entry in methods if entry["method_id"] in selected_ids]

    manifest = {
        "primary_fact_metric": choose_primary_fact_metric(),
        "sample_limit": args.sample_limit,
        "methods": [],
    }

    for entry in methods:
        command, missing = build_command_for_method(entry, sample_limit=args.sample_limit)
        has_result = int(entry.get("current_samples") or 0) >= args.sample_limit
        should_skip = args.skip_existing and has_result
        manifest["methods"].append(
            {
                "method_id": entry["method_id"],
                "status": entry.get("status", ""),
                "already_has_result": has_result,
                "will_skip": should_skip,
                "missing_prerequisites": missing,
                "command": command,
            }
        )

        if not args.execute or should_skip or missing:
            continue

        print(f"Running {entry['method_id']} ...")
        subprocess.run(command, cwd=str(ROOT), check=True)

    manifest_path = output_dir / "unified_eval_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(manifest_path)


if __name__ == "__main__":
    main()
