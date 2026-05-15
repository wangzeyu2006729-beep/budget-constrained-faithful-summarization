"""统一汇总 BART 实验结果，补充运行时间和权重元数据。

功能：
  1. 扫描 bart/results/ 下所有结果文件
  2. 从每个结果文件的 config_header 提取运行时间、权重、方法等信息
  3. 生成统一的结果汇总 CSV，包含：
     - method, objective, beam_size, split, num_samples
     - w_rouge, w_minicheck, w_redundancy (原始权重)
     - effective_w_rouge, effective_w_minicheck, effective_w_redundancy (有效权重)
     - ROUGE-1/2/L, BERTScore, MiniCheck, FactCC
     - Runtime_sec (运行时间)
     - result_file (结果文件路径)
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "bart" / "results"
OUTPUT_CSV = ROOT / "bart" / "results" / "consolidated_results_with_metadata.csv"

FIELDNAMES = [
    "method",
    "objective",
    "beam_size",
    "split",
    "num_samples",
    "w_rouge",
    "w_minicheck",
    "w_redundancy",
    "effective_w_rouge",
    "effective_w_minicheck",
    "effective_w_redundancy",
    "ROUGE-1",
    "ROUGE-2",
    "ROUGE-L",
    "BERTScore_F1",
    "MiniCheck",
    "FactCC",
    "Runtime_sec",
    "result_file",
]


def _extract_float(text: str, pattern: str, default: str = "") -> str:
    """从文本中用正则提取浮点数。"""
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return default


def _parse_config_header(header: str) -> dict[str, str]:
    """从 config_header 提取关键信息。"""
    result = {}
    
    # 提取 Method
    match = re.search(r"Method: (\S+)", header)
    if match:
        result["method"] = match.group(1)
    
    # 提取 Objective variant
    match = re.search(r"Objective variant: ([^\n]+)", header)
    if match:
        result["objective"] = match.group(1).strip()
    
    # 提取 Beam size
    match = re.search(r"Beam size: (\d+)", header)
    if match:
        result["beam_size"] = match.group(1)
    
    # 提取 Split
    match = re.search(r"Split: (\S+)", header)
    if match:
        result["split"] = match.group(1)
    
    # 提取 Samples
    match = re.search(r"Samples: (\d+)", header)
    if match:
        result["num_samples"] = match.group(1)
    
    # 提取 Runtime total seconds
    match = re.search(r"Runtime total seconds: ([\d.]+)", header)
    if match:
        result["Runtime_sec"] = match.group(1)
    
    # 提取 Tri-metric weights (原始权重)
    match = re.search(r"Tri-metric weights: ([^\n]+)", header)
    if match:
        weights_str = match.group(1)
        # 解析 "rouge=X.XXXX, minicheck=Y.YYYY, redundancy=Z.ZZZZ" 或类似格式
        rouge_match = re.search(r"(?:rouge|consensus)=([\d.]+)", weights_str)
        minicheck_match = re.search(r"minicheck=([\d.]+)", weights_str)
        redundancy_match = re.search(r"redundancy=([\d.]+)", weights_str)
        
        if rouge_match:
            result["w_rouge"] = rouge_match.group(1)
        if minicheck_match:
            result["w_minicheck"] = minicheck_match.group(1)
        if redundancy_match:
            result["w_redundancy"] = redundancy_match.group(1)
    
    return result


def _parse_metrics_section(content: str) -> dict[str, str]:
    """从结果文件的 metrics 部分提取评估指标。"""
    result = {}
    
    # 提取 ROUGE 指标
    rouge1_match = re.search(r"rouge1\s+.*?F1=([\d.]+)%", content)
    if rouge1_match:
        result["ROUGE-1"] = rouge1_match.group(1)
    
    rouge2_match = re.search(r"rouge2\s+.*?F1=([\d.]+)%", content)
    if rouge2_match:
        result["ROUGE-2"] = rouge2_match.group(1)
    
    rougeL_match = re.search(r"rougeL\s+.*?F1=([\d.]+)%", content)
    if rougeL_match:
        result["ROUGE-L"] = rougeL_match.group(1)
    
    # 提取 BERTScore
    bert_match = re.search(r"BERTScore.*?F1=([\d.]+)%", content)
    if bert_match:
        result["BERTScore_F1"] = bert_match.group(1)
    
    # 提取 MiniCheck
    minicheck_match = re.search(r"MiniCheck.*?SummaryAvgConsistent: ([\d.]+)%", content)
    if minicheck_match:
        result["MiniCheck"] = minicheck_match.group(1)
    
    # 提取 FactCC
    factcc_match = re.search(r"FactCC.*?SentenceAvgCorrect: ([\d.]+)%", content)
    if factcc_match:
        result["FactCC"] = factcc_match.group(1)
    
    return result


def _process_result_file(result_file: Path) -> Optional[dict[str, str]]:
    """处理单个结果文件，提取所有元数据。"""
    try:
        content = result_file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  [ERROR] Failed to read {result_file}: {e}")
        return None
    
    # 分离 config_header 和 metrics 部分
    parts = content.split("="*60)
    if len(parts) < 2:
        print(f"  [WARN] {result_file} 格式不标准，跳过")
        return None
    
    config_header = parts[0]
    metrics_section = "\n".join(parts[1:])
    
    # 提取配置和指标
    row = _parse_config_header(config_header)
    row.update(_parse_metrics_section(metrics_section))
    
    # 补充结果文件路径（相对于 ROOT）
    try:
        rel_path = result_file.relative_to(ROOT)
        row["result_file"] = str(rel_path)
    except ValueError:
        row["result_file"] = str(result_file)
    
    return row


def main() -> None:
    """主函数：扫描所有结果文件并生成汇总 CSV。"""
    if not RESULTS_DIR.exists():
        print(f"Error: {RESULTS_DIR} does not exist")
        return
    
    # 找出所有 *_results.txt 文件
    result_files = sorted(RESULTS_DIR.rglob("*_results.txt"))
    print(f"Found {len(result_files)} result files in {RESULTS_DIR}")
    
    rows = []
    for result_file in result_files:
        print(f"Processing: {result_file.relative_to(ROOT)}")
        row = _process_result_file(result_file)
        if row:
            rows.append(row)
    
    # 写入汇总 CSV
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, restval="")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    
    print(f"\nWrote {len(rows)} rows to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
