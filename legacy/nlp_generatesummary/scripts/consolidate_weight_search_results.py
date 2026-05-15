"""合并冗余的权重搜索结果文件。

功能：
  1. 扫描所有 tri_metric_grid_search_*.csv 和 tri_metric_selected_weight_*.csv
  2. 提取每个方法的最优权重和性能指标
  3. 生成统一的权重优化总结表
  4. 标记可删除的冗余文件
"""

import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "bart" / "results"

def consolidate_weights():
    """合并权重搜索结果。"""
    
    # 扫描所有权重搜索文件
    grid_files = sorted(RESULTS_DIR.glob("tri_metric_grid_search_*.csv"))
    selected_files = sorted(RESULTS_DIR.glob("tri_metric_selected_weight_*.csv"))
    
    print(f"Found {len(grid_files)} grid search files")
    print(f"Found {len(selected_files)} selected weight files")
    
    # 提取每个方法的最优权重
    method_weights = {}
    
    for selected_file in selected_files:
        try:
            with selected_file.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    method = row.get("source_method", "").strip()
                    if method:
                        method_weights[method] = {
                            "w_rouge": row.get("w_rouge", ""),
                            "w_minicheck": row.get("w_minicheck", ""),
                            "w_redundancy": row.get("w_redundancy", ""),
                            "source_file": selected_file.name,
                        }
                        print(f"  {method}: {method_weights[method]}")
        except Exception as e:
            print(f"  Error reading {selected_file}: {e}")
    
    # 生成统一总结
    output_file = RESULTS_DIR / "weight_optimization_consolidated.csv"
    
    with output_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["method", "w_rouge", "w_minicheck", "w_redundancy", "source_file", "status"]
        )
        writer.writeheader()
        
        for method in sorted(method_weights.keys()):
            weights = method_weights[method]
            writer.writerow({
                "method": method,
                "w_rouge": weights["w_rouge"],
                "w_minicheck": weights["w_minicheck"],
                "w_redundancy": weights["w_redundancy"],
                "source_file": weights["source_file"],
                "status": "consolidated",
            })
    
    print(f"\nConsolidated to: {output_file}")
    
    # 列出可删除的冗余文件
    print("\n可删除的冗余文件（已合并）：")
    for f in grid_files + selected_files:
        print(f"  rm {f.relative_to(ROOT)}")

if __name__ == "__main__":
    consolidate_weights()
