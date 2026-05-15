from __future__ import annotations

import argparse
import json
import os
import stat
import shutil
import subprocess
from pathlib import Path


DEFAULT_MOVE_CANDIDATES = [
    "AlignScore-main",
    "alignscore_ckpt",
    "apricot-master",
    "BARTScore-main",
    "bert_score-master",
    "DPPy-master",
    "MiniCheck-main",
    "minicheck_ckpts",
    "FactScoreLite-main",
    "NLP-Extractive-NEWS-summarization-using-MMR-master",
    "rebel-main",
    "factCC-master",
    "everything-claude-code-main",
    "__MACOSX",
]


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_assets_root() -> Path:
    root = project_root()
    return root.parent / "NLM_assets" / root.name


def local_config_file() -> Path:
    return project_root() / ".nlm_assets.json"


def tracked_count(relative_name: str) -> int:
    result = subprocess.run(
        ["git", "ls-files", "--", relative_name],
        cwd=project_root(),
        capture_output=True,
        text=True,
        check=True,
    )
    return len([line for line in result.stdout.splitlines() if line.strip()])


def write_local_config(assets_root: Path) -> None:
    payload = {"assets_root": str(assets_root.resolve())}
    local_config_file().write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _handle_remove_readonly(func, path, excinfo) -> None:
    _ = excinfo
    os.chmod(path, stat.S_IWRITE)
    func(path)


def remove_tree(path: Path) -> None:
    if not path.exists():
        return
    try:
        shutil.rmtree(path, onexc=_handle_remove_readonly)
    except OSError:
        if os.name != "nt":
            raise
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"Remove-Item -LiteralPath '{path}' -Recurse -Force",
            ],
            check=True,
        )

    if path.exists() and os.name == "nt":
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"Remove-Item -LiteralPath '{path}' -Recurse -Force",
            ],
            check=True,
        )


def move_directory(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    if os.name == "nt":
        destination.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [
                "robocopy",
                str(source),
                str(destination),
                "/E",
                "/MOVE",
                "/NFL",
                "/NDL",
                "/NJH",
                "/NJS",
                "/NP",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode >= 8:
            raise RuntimeError(
                f"robocopy failed for {source} -> {destination}: "
                f"{result.stdout}\n{result.stderr}"
            )
        if source.exists():
            remove_tree(source)
        return

    shutil.move(str(source), str(destination))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Move external assets out of the Git worktree.")
    parser.add_argument(
        "--assets-root",
        type=Path,
        default=default_assets_root(),
        help="Destination root for external assets.",
    )
    parser.add_argument(
        "--include-tracked",
        action="store_true",
        help="Also move directories that are still tracked by Git.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without moving anything.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = project_root()
    assets_root = args.assets_root.resolve()

    moved: list[str] = []
    skipped: list[str] = []

    if not args.dry_run:
        assets_root.mkdir(parents=True, exist_ok=True)
        write_local_config(assets_root)

    for name in DEFAULT_MOVE_CANDIDATES:
        source = repo_root / name
        destination = assets_root / name

        if not source.exists():
            skipped.append(f"{name}: missing")
            continue

        tracked = tracked_count(name)
        if tracked and not args.include_tracked:
            skipped.append(f"{name}: skipped ({tracked} tracked files)")
            continue

        if args.dry_run:
            moved.append(f"{name}: would move to {destination}")
            continue

        move_directory(source, destination)
        moved.append(f"{name}: moved to {destination}")

    print(f"Assets root: {assets_root}")
    print("")
    print("Moved:")
    if moved:
        for item in moved:
            print(f"  - {item}")
    else:
        print("  - none")

    print("")
    print("Skipped:")
    if skipped:
        for item in skipped:
            print(f"  - {item}")
    else:
        print("  - none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
