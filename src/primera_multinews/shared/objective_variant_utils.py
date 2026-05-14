"""
FactCC 句子级 Utility 计算工具。

【用途】
在 minicheck_only 和 minicheck_redundancy 变体中，
我们不用 ROUGE 而是用 FactCC 模型来给每个候选句子打分。
FactCC 的输出是 P(CORRECT | article, sentence)，
即"这个句子相对于原文是事实正确的"概率。

【和 FactCC 评估的区别】
- objective_variant_utils.py（本文件）：用 FactCC 给单句打 utility 分，
  在优化选择阶段使用，帮助选择器挑出更"忠实"的句子。
- factcc_eval_utils.py：在最终评估阶段，对生成的完整摘要做 FactCC 评分。

两者使用同一个 FactCC 模型，但调用时机和粒度不同。
"""

from __future__ import annotations

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


FACTCC_MODEL_NAME = "manueldeprada/FactCC"


def load_factcc_model(device, model_name: str = FACTCC_MODEL_NAME):
    """
    加载 FactCC 分类器。

    FactCC 是一个二分类模型（CORRECT / INCORRECT），
    输入是 (article, sentence) 对，输出两个类别的概率。

    返回:
        (tokenizer, model, correct_id):
        - tokenizer: 文本分词器
        - model: FactCC 模型（已移到 GPU 并设为 eval 模式）
        - correct_id: CORRECT 标签在模型输出中的索引
    """
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name).to(device)
    model.eval()

    # 找到 CORRECT 标签对应的 ID
    # 不同版本的模型可能 label 顺序不同，所以需要动态查找
    correct_id = model.config.label2id.get("CORRECT")
    if correct_id is None:
        for idx, label in model.config.id2label.items():
            if label == "CORRECT":
                correct_id = int(idx)
                break
    if correct_id is None:
        correct_id = 0  # 兜底默认值

    return tokenizer, model, int(correct_id)


def compute_factcc_scores(
    unique_sentences,
    article,
    tokenizer,
    model,
    device,
    correct_id,
    batch_size: int = 16,
    max_length: int = 512,
):
    """
    计算每个候选句子的 FactCC CORRECT 概率，作为 utility 分数。

    【流程】
    1. 把所有 (article, sentence) 对按 batch_size 分批
    2. 每批：tokenize → 送入模型 → softmax → 取 CORRECT 概率
    3. 返回每句的概率值列表

    参数:
        unique_sentences: 候选句子列表
        article: 原始文章文本
        tokenizer: FactCC 的分词器
        model: FactCC 模型
        device: 计算设备
        correct_id: CORRECT 类别的索引
        batch_size: 批处理大小
        max_length: 最大 token 长度（FactCC 用的是 512）

    返回:
        scores: 每个句子的 P(CORRECT) 列表
    """
    if not unique_sentences:
        return []

    scores = []
    for start in range(0, len(unique_sentences), batch_size):
        batch_sentences = unique_sentences[start:start + batch_size]
        batch_articles = [article] * len(batch_sentences)

        # tokenize：article 做 premise，sentence 做 hypothesis
        # truncation="only_first" 只截断 article（premise），保留完整的 sentence
        inputs = tokenizer(
            batch_articles,
            batch_sentences,
            return_tensors="pt",
            padding="max_length",
            truncation="only_first",
            max_length=max_length,
        ).to(device)

        with torch.no_grad():
            logits = model(**inputs).logits.float()  # [batch_size, 2]

        # softmax 得到概率，取 CORRECT 类别
        probs = torch.softmax(logits, dim=-1)[:, correct_id]  # [batch_size]
        scores.extend(probs.detach().cpu().tolist())

    return scores


def compute_identity_redundancy_matrix(unique_sentences):
    """
    返回单位矩阵作为冗余矩阵的占位符（用于"不惩罚冗余"的变体）。

    对角线 = 1（自己和自己完全冗余），其余 = 0（不认为任何两句有冗余）。
    """
    n = len(unique_sentences)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        matrix[i][i] = 1.0
    return matrix
