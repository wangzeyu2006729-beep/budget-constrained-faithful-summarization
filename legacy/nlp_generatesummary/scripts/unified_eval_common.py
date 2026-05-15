from __future__ import annotations

import ast
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BART_ROOT = ROOT / "bart"
PAPERS_ROOT = ROOT / "papers" / "复现baseline"
SCRIPTS_ROOT = ROOT / "scripts"
BART_RESULTS_ROOT = BART_ROOT / "results"
UNIFIED_RESULTS_ROOT = BART_RESULTS_ROOT / "unified_eval"

PREFERRED_SUMMARY_CSV_PATH = BART_RESULTS_ROOT / "summary_metrics_beam5_hfrouge.csv"
LEGACY_SUMMARY_CSV_PATH = BART_RESULTS_ROOT / "summary_metrics_beam3_hfrouge.csv"
SUMMARY_CSV_PATH = PREFERRED_SUMMARY_CSV_PATH if PREFERRED_SUMMARY_CSV_PATH.exists() else LEGACY_SUMMARY_CSV_PATH
RUN_PY_PATH = BART_ROOT / "run.py"
BART_ARGS_PY_PATH = BART_ROOT / "cli" / "args.py"
CONFIG_PY_PATH = BART_ROOT / "core" / "config.py"
MBR_PY_PATH = BART_ROOT / "opt_selectors" / "mbr.py"
PARETO_PY_PATH = BART_ROOT / "opt_selectors" / "pareto.py"
METADATA_PATH = SCRIPTS_ROOT / "unified_method_metadata.json"
PROJECT_VENV_PY = ROOT / ".venv" / "bin" / "python"
THIRD_PARTY_ROOT = Path("/path/to/NLM_data/third_party")
SIMCLS_ROOT = THIRD_PARTY_ROOT / "SimCLS-main"
SIMCLS_REPRO_ROOT = PAPERS_ROOT / "simcls_reproduction"
BRIO_ROOT = THIRD_PARTY_ROOT / "BRIO-main"

SERVER_METHOD_SOURCE_DIRS = {
    "lexisem": PAPERS_ROOT / "lexisem_reproduction",
    "simcls": SIMCLS_REPRO_ROOT,
    "brio_ctr": PAPERS_ROOT / "brio_ctr_reproduction",
    "summa_reranker": PAPERS_ROOT / "summa_reranker_cnndm_second_stage_reranker",
    "factedit": PAPERS_ROOT / "FACTEDIT",
    "consum_fenice_0_75": PAPERS_ROOT / "consum_cnndm_second_stage_reranker",
    "submodular_budgeted": PAPERS_ROOT / "submodular_greedy",
    "submodular_acl2011": PAPERS_ROOT / "submodular_greedy",
}


OBJECTIVE_LABEL_TO_ID = {
    "ROUGE only": "rouge_only",
    "ROUGE + Redundancy": "rouge_redundancy",
    "MiniCheck only": "minicheck_only",
    "MiniCheck + Redundancy": "minicheck_redundancy",
    "Summary-level MBR": "summary_mbr",
    "Summary-level PARETO": "summary_pareto",
}

PROJECT_METHODS = {"ilp", "mmr", "dpp", "submodular", "lns", "mbr", "pareto"}
OBJECTIVE_METHODS = {"ilp", "mmr", "dpp", "submodular", "lns"}
RUNPY_METHOD_CHOICES_FALLBACK = ["ilp", "mmr", "dpp", "submodular", "lns", "mbr", "pareto", "baseline_raw", "baseline3"]
REPRO_DIR_TO_ID = {
    "lexisem_reproduction": "lexisem",
    "simcls_reproduction": "simcls",
    "brio_ctr_reproduction": "brio_ctr",
    "summa_reranker_reproduction": "summa_reranker",
    "factedit_reproduction": "factedit",
    "consum_reproduction": "consum_fenice_0_75",
}


ROUGE_F1_RE = re.compile(r"^\s*(rouge1|rouge2|rougeL|rougeLsum)\s+F1=([-\d.]+)%$")
ROUGE_PRF_RE = re.compile(
    r"^\s*(rouge1|rouge2|rougeL|rougeLsum)\s+Precision=([-\d.]+)%\s+Recall=([-\d.]+)%\s+F1=([-\d.]+)%$"
)
BERTSCORE_RE = re.compile(r"^\s*Precision=([-\d.]+)%\s+Recall=([-\d.]+)%\s+F1=([-\d.]+)%$")
BARTSCORE_REF_RE = re.compile(r"^\s*ref->hyp:\s*([-\d.]+)$")
BARTSCORE_HYP_RE = re.compile(r"^\s*hyp->ref:\s*([-\d.]+)$")
BARTSCORE_SRC_RE = re.compile(r"^\s*src->hyp:\s*([-\d.]+)$")
ENTAILMENT_RE = re.compile(r"^\s*Entailment:\s*([-\d.]+)%$")
FACTCC_RE = re.compile(r"^\s*SentenceAvgCorrect:\s*([-\d.]+)%$")
MINICHECK_RE = re.compile(r"^\s*SummaryAvgConsistent:\s*([-\d.]+)%$")
ALIGNSCORE_RE = re.compile(r"^\s*SummaryAvg:\s*([-\d.]+)%$")
MOVERSCORE_RE = re.compile(r"^\s*MoverScore:\s*([-\d.]+)%$")
ENT_DAE_RE = re.compile(r"^\s*Ent-DAE:\s*([-\d.]+)%$")
MENLI_RE = re.compile(r"^\s*MENLI:\s*([-\d.]+)%$")
FENICE_RE = re.compile(r"^\s*FENICE:\s*([-\d.]+)%$")
SAMPLES_RE = re.compile(r"^Samples:\s*(\d+)")
SPLIT_RE = re.compile(r"^Split:\s*(train|validation|test)")
SUITE_RE = re.compile(r"^Evaluation suite:\s*(.+)$")


def ensure_output_dir(path: Path | None = None) -> Path:
    target = path or UNIFIED_RESULTS_ROOT
    target.mkdir(parents=True, exist_ok=True)
    return target


def _preferred_python(*candidates: Path) -> str:
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return sys.executable or "python3"


def _normalize_metadata_path(raw_path: Any) -> Any:
    if not isinstance(raw_path, str):
        return raw_path

    normalized = raw_path.replace("\\", "/")
    if "NLM_generatesummary/" not in normalized:
        return raw_path

    relative = normalized.split("NLM_generatesummary/", 1)[1]
    if relative.startswith("SimCLS-main/"):
        return str(SIMCLS_ROOT / relative.split("SimCLS-main/", 1)[1])
    if relative.startswith("BRIO-main/"):
        return str(BRIO_ROOT / relative.split("BRIO-main/", 1)[1])
    return str(ROOT / relative)


def _normalize_metadata_entry(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    if isinstance(normalized.get("source_dir"), str):
        normalized["source_dir"] = _normalize_metadata_path(normalized["source_dir"])

    required_paths = normalized.get("required_paths")
    if isinstance(required_paths, dict):
        normalized["required_paths"] = {
            label: _normalize_metadata_path(raw_path) for label, raw_path in required_paths.items()
        }

    return normalized


def load_metadata() -> dict[str, Any]:
    if not METADATA_PATH.exists():
        return {}
    payload = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    return {method_id: _normalize_metadata_entry(meta) for method_id, meta in payload.items()}


def _to_float(value: Any) -> float | None:
    if value in (None, "", "—", "-", "_"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class _LiteralResolver:
    def __init__(self) -> None:
        self.env: dict[str, Any] = {}

    def eval(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return self.env[node.id]
        if isinstance(node, ast.List):
            return [self.eval(item) for item in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(self.eval(item) for item in node.elts)
        if isinstance(node, ast.Set):
            return {self.eval(item) for item in node.elts}
        if isinstance(node, ast.Dict):
            return {self.eval(k): self.eval(v) for k, v in zip(node.keys, node.values)}
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -self.eval(node.operand)
        raise ValueError(f"Unsupported node: {ast.dump(node)}")


def extract_named_constants(path: Path, names: set[str]) -> dict[str, Any]:
    resolver = _LiteralResolver()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: dict[str, Any] = {}
    for stmt in tree.body:
        if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
            continue
        target = stmt.targets[0].id
        try:
            value = resolver.eval(stmt.value)
        except Exception:
            continue
        resolver.env[target] = value
        if target in names:
            found[target] = value
    return found


def discover_runpy_methods() -> list[dict[str, Any]]:
    constants = extract_named_constants(BART_ARGS_PY_PATH, {"ALL_METHODS"})
    objective_variants = list(
        extract_named_constants(CONFIG_PY_PATH, {"OBJECTIVE_VARIANTS"}).get("OBJECTIVE_VARIANTS", {}).keys()
    )
    methods = list(constants.get("ALL_METHODS") or RUNPY_METHOD_CHOICES_FALLBACK)
    if not objective_variants:
        objective_variants = ["rouge_only", "rouge_redundancy", "minicheck_only", "minicheck_redundancy"]

    discovered: list[dict[str, Any]] = []
    for method in methods:
        if method in OBJECTIVE_METHODS:
            for objective in objective_variants:
                discovered.append(
                    {
                        "method_id": f"{method}_{objective}",
                        "runner_kind": "bart_run",
                        "declared_method": method,
                        "declared_objective": objective,
                    }
                )
        elif method == "mbr":
            discovered.append(
                {
                    "method_id": "mbr_summary_mbr",
                    "runner_kind": "bart_run",
                    "declared_method": method,
                    "declared_objective": None,
                }
            )
        elif method == "pareto":
            discovered.append(
                {
                    "method_id": "pareto_summary_pareto",
                    "runner_kind": "bart_run",
                    "declared_method": method,
                    "declared_objective": None,
                }
            )
        else:
            discovered.append(
                {
                    "method_id": method,
                    "runner_kind": "bart_run",
                    "declared_method": method,
                    "declared_objective": None,
                }
            )
    return discovered


def discover_reproduction_methods() -> list[dict[str, Any]]:
    discovered: list[dict[str, Any]] = []
    seen: set[str] = set()

    for method_id, source_dir in SERVER_METHOD_SOURCE_DIRS.items():
        if not source_dir.exists():
            continue
        discovered.append(
            {
                "method_id": method_id,
                "runner_kind": "paper_reproduction",
                "source_dir": str(source_dir),
            }
        )
        seen.add(method_id)

    if not PAPERS_ROOT.exists():
        return discovered

    for directory in sorted(PAPERS_ROOT.iterdir()):
        if not directory.is_dir():
            continue
        method_id = REPRO_DIR_TO_ID.get(directory.name)
        if method_id and method_id not in seen:
            discovered.append(
                {
                    "method_id": method_id,
                    "runner_kind": "paper_reproduction",
                    "source_dir": str(directory),
                }
            )
    return discovered


def default_display_name(method_id: str) -> str:
    return method_id


def normalize_bart_csv_row(row: dict[str, str]) -> dict[str, Any]:
    method = row["Method"]
    objective = row["Objective"]
    declared_objective = None

    if method in {"baseline_raw", "baseline3"}:
        method_id = method
    elif method in {"mbr", "pareto"}:
        objective_id = OBJECTIVE_LABEL_TO_ID[objective]
        method_id = f"{method}_{objective_id}"
    else:
        objective_id = OBJECTIVE_LABEL_TO_ID[objective]
        method_id = f"{method}_{objective_id}"
        declared_objective = objective_id

    return {
        "method_id": method_id,
        "display_name": default_display_name(method_id),
        "method_type": "user_method" if method in PROJECT_METHODS else "bart_baseline",
        "paper_source": (
            "Local project (BART + beam search + combinatorial optimization)"
            if method in PROJECT_METHODS
            else "Local project baseline"
        ),
        "project_family": "bart_beam_combopt" if method in PROJECT_METHODS else None,
        "runner_kind": "bart_run",
        "declared_method": method,
        "declared_objective": declared_objective,
        "entrypoint": str(RUN_PY_PATH),
        "status": "runnable",
        "current_result_file": str(SUMMARY_CSV_PATH),
        "current_samples": 500,
        "split": row["Split"],
        "notes": row["Objective"],
        "current_metrics": {
            "rouge1": _to_float(row.get("ROUGE-1")),
            "rouge2": _to_float(row.get("ROUGE-2")),
            "rougeL": _to_float(row.get("ROUGE-L")),
            "rougeLsum": _to_float(row.get("ROUGE-Lsum")),
            "bertscore_f1": _to_float(row.get("BERTScore_F1")),
            "bartscore_src": _to_float(row.get("BARTScore_src")),
            "nli_entailment": _to_float(row.get("NLI_Entailment")),
            "factcc": _to_float(row.get("FactCC")),
            "minicheck": _to_float(row.get("MiniCheck")),
            "alignscore": _to_float(row.get("AlignScore")),
        },
    }


def discover_bart_csv_results() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    if not SUMMARY_CSV_PATH.exists():
        return rows
    with SUMMARY_CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("Split") != "test":
                continue
            parsed = normalize_bart_csv_row(row)
            rows.setdefault(parsed["method_id"], parsed)
    return rows


def parse_metrics_from_text(text: str) -> dict[str, Any]:
    parsed: dict[str, Any] = {"current_metrics": {}}
    in_bertscore = False

    for line in text.splitlines():
        match = SAMPLES_RE.search(line)
        if match:
            parsed["current_samples"] = int(match.group(1))
            continue

        match = SPLIT_RE.search(line)
        if match:
            parsed["split"] = match.group(1)
            continue

        match = SUITE_RE.search(line)
        if match:
            parsed["evaluation_suite"] = match.group(1).strip()
            continue

        match = ROUGE_F1_RE.search(line)
        if match:
            parsed["current_metrics"][match.group(1)] = float(match.group(2))
            continue

        match = ROUGE_PRF_RE.search(line)
        if match:
            parsed["current_metrics"][match.group(1)] = float(match.group(4))
            continue

        if line.startswith("BERTScore"):
            in_bertscore = True
            continue

        if in_bertscore:
            match = BERTSCORE_RE.search(line)
            if match:
                parsed["current_metrics"]["bertscore_precision"] = float(match.group(1))
                parsed["current_metrics"]["bertscore_recall"] = float(match.group(2))
                parsed["current_metrics"]["bertscore_f1"] = float(match.group(3))
                in_bertscore = False
            continue

        for regex, key in (
            (BARTSCORE_REF_RE, "bartscore_ref2hyp"),
            (BARTSCORE_HYP_RE, "bartscore_hyp2ref"),
            (BARTSCORE_SRC_RE, "bartscore_src"),
            (ENTAILMENT_RE, "nli_entailment"),
            (FACTCC_RE, "factcc"),
            (MINICHECK_RE, "minicheck"),
            (ALIGNSCORE_RE, "alignscore"),
            (MOVERSCORE_RE, "moverscore"),
            (ENT_DAE_RE, "ent_dae"),
            (MENLI_RE, "menli"),
            (FENICE_RE, "fenice"),
        ):
            match = regex.search(line)
            if match:
                parsed["current_metrics"][key] = float(match.group(1))
                break

    return parsed


def parse_result_file(path: Path) -> dict[str, Any] | None:
    try:
        if path.suffix.lower() == ".json" and path.name == "aggregate_results.json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            return parse_consum_report(path, payload)
        if path.suffix.lower() != ".txt":
            return None
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    parsed = parse_metrics_from_text(text)
    if not parsed.get("current_metrics"):
        return None
    parsed["current_result_file"] = str(path)
    return parsed


def parse_consum_report(path: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
    systems = payload.get("systems", {})
    main = systems.get("fenice_0.75") or systems.get("consum") or {}
    if not main:
        return None
    metrics = {
        "rouge1": _to_float(main.get("rouge1") or main.get("rouge_1")),
        "rouge2": _to_float(main.get("rouge2") or main.get("rouge_2")),
        "rougeL": _to_float(main.get("rougeL") or main.get("rouge_l")),
        "bertscore_f1": _to_float(main.get("bertscore") or main.get("bertscore_f1")),
        "menli": _to_float(main.get("menli")),
        "fenice": _to_float(main.get("fenice")),
    }
    metrics = {key: value for key, value in metrics.items() if value is not None}
    if not metrics:
        return None
    return {
        "current_result_file": str(path),
        "current_samples": payload.get("num_samples"),
        "split": payload.get("split", "test"),
        "evaluation_suite": "paper_metrics",
        "current_metrics": metrics,
    }


def find_best_available_result(directory: Path) -> dict[str, Any] | None:
    if not directory.exists():
        return None

    best: dict[str, Any] | None = None
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        if path.name in {"train_metadata.json", "best_metrics.json"}:
            continue
        parsed = parse_result_file(path)
        if parsed is None:
            continue
        samples = int(parsed.get("current_samples") or 0)
        if best is None or samples > int(best.get("current_samples") or 0):
            best = parsed
    return best


def metric_value(entry: dict[str, Any] | None, metric_name: str) -> float | None:
    if not entry:
        return None
    return _to_float(entry.get("current_metrics", {}).get(metric_name))


def format_score(value: float | None) -> str:
    return "" if value is None else f"{value:.2f}"


def choose_primary_fact_metric() -> dict[str, Any]:
    reasons: list[str] = []
    config_text = CONFIG_PY_PATH.read_text(encoding="utf-8", errors="replace")
    mbr_text = MBR_PY_PATH.read_text(encoding="utf-8", errors="replace")
    pareto_text = PARETO_PY_PATH.read_text(encoding="utf-8", errors="replace")

    if "minicheck_only" in config_text and "minicheck_redundancy" in config_text:
        reasons.append("MiniCheck is exposed as two first-class objective variants in bart/shared/config.py.")
    if "MBR_MINICHECK_WEIGHT" in config_text and "compute_minicheck_summary_scores" in mbr_text:
        reasons.append("Summary-level MBR explicitly combines consensus with MiniCheck.")
    if "MiniCheck" in pareto_text and "minicheck" in pareto_text:
        reasons.append("Pareto summary selection prioritizes MiniCheck before coverage and redundancy.")

    return {
        "name": "MiniCheck",
        "metric_key": "minicheck",
        "secondary_metrics": ["factcc"],
        "reasons": reasons,
    }


def summarize_paper_reference(entry: dict[str, Any]) -> str:
    reference = entry.get("paper_reference") or {}
    return reference.get("display", "")


def comparable_500(entry: dict[str, Any], sample_limit: int = 500, fact_key: str = "minicheck") -> bool:
    if int(entry.get("current_samples") or 0) < sample_limit:
        return False
    return metric_value(entry, fact_key) is not None


def build_markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    header = "| " + " | ".join(title for title, _ in columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = ["| " + " | ".join(str(row.get(key, "")) for _, key in columns) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def sort_methods_for_report(entries: list[dict[str, Any]], primary_fact_key: str) -> list[dict[str, Any]]:
    def sort_key(item: dict[str, Any]) -> tuple[float, float, str]:
        fact = metric_value(item, primary_fact_key)
        rouge = metric_value(item, "rouge1")
        return (
            1 if fact is None else 0,
            1 if int(item.get("current_samples") or 0) < 500 else 0,
            0 if fact is None else -fact,
            0 if rouge is None else -rouge,
            item["method_id"],
        )

    return sorted(entries, key=sort_key)


def _load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _append_missing(missing: list[str], label: str, path: Path | None) -> None:
    if path is None or not path.exists():
        missing.append(f"{label}: {path}")


def _result_search_dirs(method_id: str, entry: dict[str, Any]) -> list[Path]:
    source_dir = Path(entry["source_dir"]) if entry.get("source_dir") else None
    if source_dir is None:
        return []
    if method_id == "factedit":
        return [source_dir / "outputs", source_dir / "checkpoints" / "correction_cnndm"]
    if method_id == "consum_fenice_0_75":
        return [source_dir / "artifacts" / "reranked", source_dir / "artifacts" / "evaluation"]
    if method_id == "summa_reranker":
        return [source_dir / "artifacts" / "reranked", source_dir / "artifacts" / "evaluation"]
    if method_id == "simcls":
        return [source_dir / "outputs"]
    return [source_dir / "outputs"]


def build_command_for_method(entry: dict[str, Any], sample_limit: int = 500) -> tuple[list[str], list[str]]:
    method_id = entry["method_id"]
    runner_kind = entry.get("runner_kind")
    metadata = entry.get("metadata", {})
    missing: list[str] = []
    project_python = _preferred_python(PROJECT_VENV_PY)

    if runner_kind == "bart_run":
        method = entry.get("declared_method")
        objective = entry.get("declared_objective")
        cmd = [
            project_python,
            str(RUN_PY_PATH),
            "--method",
            str(method),
            "--split",
            "test",
            "--num-samples",
            str(sample_limit),
        ]
        if method in OBJECTIVE_METHODS and objective:
            cmd.extend(["--objective", str(objective)])
        if method in PROJECT_METHODS or method in {"baseline3", "baseline_raw"}:
            cmd.extend(["--beam-size", "5"])
        return cmd, missing

    if method_id == "lexisem":
        source_dir = Path(entry.get("source_dir") or SERVER_METHOD_SOURCE_DIRS["lexisem"])
        launcher = source_dir / "run_unified.sh"
        candidate_dir = ROOT / "LexiSem-main" / "results" / "result_cnndm" / "candidate"
        reference_dir = ROOT / "LexiSem-main" / "results" / "result_cnndm" / "reference"
        article_dir = _first_existing(
            [
                ROOT / "downloads" / "lexisem" / "cnndm" / "test",
                ROOT / "downloads" / "lexisem" / "test" / "test",
            ]
        )
        _append_missing(missing, "launcher", launcher)
        _append_missing(missing, "candidate_dir", candidate_dir)
        _append_missing(missing, "reference_dir", reference_dir)
        _append_missing(missing, "article_dir", article_dir)
        cmd = ["bash", str(launcher)]
        if sample_limit and sample_limit > 0:
            cmd.extend(["--num-samples", str(sample_limit)])
        return cmd, missing

    if method_id == "simcls":
        source_dir = Path(entry.get("source_dir") or SERVER_METHOD_SOURCE_DIRS["simcls"])
        launcher = source_dir / "run_unified.sh"
        _append_missing(missing, "launcher", launcher)
        _append_missing(missing, "prediction_file", SIMCLS_ROOT / "output" / "test.cnndm.ours")
        _append_missing(missing, "reference_file", SIMCLS_ROOT / "output" / "test.cnndm.reference")
        _append_missing(missing, "source_dir", BRIO_ROOT / "cnndm" / "diverse" / "test")
        cmd = ["bash", str(launcher)]
        if sample_limit and sample_limit > 0:
            cmd.extend(["--num-samples", str(sample_limit)])
        return cmd, missing

    if method_id == "brio_ctr":
        source_dir = Path(entry.get("source_dir") or SERVER_METHOD_SOURCE_DIRS["brio_ctr"])
        launcher = source_dir / "run_unified.sh"
        _append_missing(missing, "launcher", launcher)
        _append_missing(missing, "brio_checkpoint", BRIO_ROOT / "cache" / "cnndm" / "model_ranking.bin")
        _append_missing(missing, "brio_test", BRIO_ROOT / "cnndm" / "diverse" / "test")
        cmd = ["bash", str(launcher)]
        if sample_limit and sample_limit > 0:
            cmd.extend(["--num-samples", str(sample_limit)])
        return cmd, missing

    if method_id == "summa_reranker":
        source_dir = Path(entry.get("source_dir") or SERVER_METHOD_SOURCE_DIRS["summa_reranker"])
        launcher = source_dir / "run_unified.sh"
        asset_report = _load_json_if_exists(source_dir / "artifacts" / "logs" / "check_cnndm_assets.json") or {}
        _append_missing(missing, "launcher", launcher)
        if not asset_report.get("launcher_manages_assets", False):
            if not asset_report.get("official_checkpoint_bin_exists", False):
                missing.append("official_checkpoint: missing")
            if not asset_report.get("official_data_root_exists", False):
                missing.append("official_data_root: missing")
            if not asset_report.get("official_summaries_root_exists", False):
                missing.append("official_summaries_root: missing")
            if not asset_report.get("official_scored_root_exists", False):
                missing.append("official_scored_root: missing")
        cmd = ["bash", str(launcher)]
        if sample_limit and sample_limit > 0:
            cmd.extend(["--num-samples", str(sample_limit)])
        return cmd, missing

    if method_id == "factedit":
        factedit_root = Path(entry.get("source_dir") or SERVER_METHOD_SOURCE_DIRS["factedit"])
        launcher = factedit_root / "run_unified.sh"
        _append_missing(missing, "launcher", launcher)
        _append_missing(missing, "correction_checkpoint", factedit_root / "checkpoints" / "correction_cnndm" / "best.ckpt")
        cmd = ["bash", str(launcher)]
        if sample_limit and sample_limit > 0:
            cmd.extend(["--num-samples", str(sample_limit)])
        return cmd, missing

    if method_id == "consum_fenice_0_75":
        source_dir = Path(entry.get("source_dir") or SERVER_METHOD_SOURCE_DIRS["consum_fenice_0_75"])
        launcher = source_dir / "run_unified.sh"
        asset_report = _load_json_if_exists(source_dir / "artifacts" / "logs" / "check_cnndm_consum_assets.json") or {}
        _append_missing(missing, "launcher", launcher)
        if not asset_report.get("data_cache", {}).get("test", False):
            missing.append("data_cache[test]: missing")
        if not asset_report.get("pseudo_reference_files", {}).get("test", False):
            missing.append("pseudo_reference_files[test]: missing")
        if not asset_report.get("score_files", {}).get("test", False):
            missing.append("score_files[test]: missing")
        if not all(asset_report.get("candidate_files", {}).get("test", {}).values()):
            missing.append("candidate_files[test]: missing")
        cmd = ["bash", str(launcher)]
        if sample_limit and sample_limit > 0:
            cmd.extend(["--num-samples", str(sample_limit)])
        return cmd, missing

    if method_id in {"submodular_budgeted", "submodular_acl2011"}:
        source_dir = Path(entry.get("source_dir") or SERVER_METHOD_SOURCE_DIRS[method_id])
        script = source_dir / "experiments" / "run_greedy.py"
        data_path = source_dir / "data" / "example_cluster.txt"
        _append_missing(missing, "script", script)
        _append_missing(missing, "data_path", data_path)
        cmd = [
            project_python,
            str(script),
            "--data_path",
            str(data_path),
            "--output_dir",
            str(source_dir / "outputs" / method_id),
        ]
        return cmd, missing

    return ["python"], ["No runner mapping found"]


def discover_methods() -> list[dict[str, Any]]:
    metadata = load_metadata()
    by_id: dict[str, dict[str, Any]] = {}

    for item in discover_runpy_methods() + discover_reproduction_methods():
        method_id = item["method_id"]
        entry = dict(item)
        meta = metadata.get(method_id, {})
        entry["metadata"] = meta
        entry.update(meta)
        entry.setdefault("display_name", default_display_name(method_id))
        by_id[method_id] = entry

    for method_id, meta in metadata.items():
        if method_id not in by_id:
            by_id[method_id] = {"method_id": method_id, "metadata": meta, **meta}
            by_id[method_id].setdefault("display_name", default_display_name(method_id))

    for method_id, result in discover_bart_csv_results().items():
        entry = by_id.setdefault(method_id, {"method_id": method_id, "metadata": metadata.get(method_id, {})})
        entry.update(metadata.get(method_id, {}))
        entry.update(result)
        entry["metadata"] = metadata.get(method_id, {})

    for method_id, entry in by_id.items():
        if method_id not in discover_bart_csv_results():
            if method_id == "submodular_acl2011":
                best = find_best_available_result(BART_RESULTS_ROOT / "submodular_acl2011_500")
            elif method_id == "submodular_budgeted":
                best = find_best_available_result(BART_RESULTS_ROOT / "submodular_budgeted_500")
                if best is None:
                    best = find_best_available_result(BART_RESULTS_ROOT / "submodular_budgeted_smoke")
            else:
                best = None
                for result_dir in _result_search_dirs(method_id, entry):
                    best = find_best_available_result(result_dir)
                    if best:
                        break
            if best:
                entry.update(best)

        entry.setdefault("current_metrics", {})
        entry.setdefault("current_samples", None)
        entry.setdefault("display_name", default_display_name(method_id))
        if method_id in SERVER_METHOD_SOURCE_DIRS:
            entry.setdefault("source_dir", str(SERVER_METHOD_SOURCE_DIRS[method_id]))

        inventory_sample_limit = 0 if method_id in {
            "brio_ctr",
            "lexisem",
            "simcls",
            "summa_reranker",
            "factedit",
            "consum_fenice_0_75",
        } else 500
        command, missing = build_command_for_method(entry, sample_limit=inventory_sample_limit)
        entry["default_command"] = " ".join(command)
        entry["missing_prerequisites"] = missing
        if len(command) >= 2 and command[1] not in {"-lc"}:
            entry.setdefault("entrypoint", command[1])
        entry.setdefault("status", "runnable" if not missing else "partial")
        entry["is_project_core_compare"] = bool(entry.get("project_family") == "bart_beam_combopt")

    return sorted(by_id.values(), key=lambda item: item["method_id"])
