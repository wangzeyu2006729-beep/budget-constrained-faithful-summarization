"""
选择器注册表：把方法名映射到对应的选择器函数。

【两类选择器】

1. 句子级选择器 (opt_selectors/sentence_level/):
   输入: (句子池, utility分数, 冗余矩阵, 预算) → 输出: 选中句子的索引列表
   - ILP, MMR, DPP

2. 摘要级选择器 (opt_selectors/summary_level/):
   输入: (句子池, 原文, 预算, minicheck_scorer, segmenter) → 输出: (索引, 摘要文本, 日志)
   - MBR, Pareto

注意：包名是 opt_selectors 而不是 selectors，
因为 Python 标准库有同名模块 selectors（用于 I/O 多路复用），
如果用 selectors 作包名会导致 socket 等标准库模块导入失败。
"""


def _lazy_import(method):
    """延迟导入选择器函数，避免在 import 阶段就加载所有依赖库。"""
    if method == "ilp":
        from opt_selectors.sentence_level.ilp import ilp_select
        return ilp_select
    elif method == "mmr":
        from opt_selectors.sentence_level.mmr import mmr_select
        return mmr_select
    elif method == "dpp":
        from opt_selectors.sentence_level.dpp import dpp_select
        return dpp_select
    else:
        raise ValueError(f"Unknown selector: {method}")


# 所有可用的选择器名称
SENTENCE_LEVEL_METHODS = {"ilp", "mmr", "dpp"}
SUMMARY_LEVEL_METHODS = set()
ALL_METHODS = SENTENCE_LEVEL_METHODS | SUMMARY_LEVEL_METHODS


def get_selector(name):
    """根据方法名返回对应的选择器函数（延迟导入）。"""
    if name not in ALL_METHODS:
        raise ValueError(f"Unknown selector: {name}. Available: {sorted(ALL_METHODS)}")
    return _lazy_import(name)


def is_summary_level(name):
    """判断该方法是否是摘要级选择器。"""
    return name in SUMMARY_LEVEL_METHODS
