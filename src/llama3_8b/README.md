# 1_llama3_8b — Meta-Llama-3.1-8B (base) 实验目录

## 概述

本目录是 `generate-then-optimize` 实验框架中 **Meta-Llama-3.1-8B base 预训练模型** 的独立实现副本。
结构和实现逻辑参考自 `1_qwen3.5_9B` 和 `1_gemma_4_e4b`，各目录互相隔离，不共享代码。

> ⚠️ 使用 base 模型而非 Instruct 版本：base 模型**没有 chat_template**，走 completion-style prompt
> （"Summarize ... Summary:\n" 让它续写）。`core/model_generation.py` 在 tokenizer 无 chat_template
> 时会自动启用 `StopOnSubstrings`，防止 base 模型续写下一条 prompt。

## 模型信息

| 参数 | 值 |
|------|---|
| HuggingFace ID | `meta-llama/Llama-3.1-8B` |
| 架构 | LlamaForCausalLM（Dense，8B 参数，带 rope_scaling llama3） |
| 上下文窗口 | **131072 tokens（128k，rope-scaled）** |
| Dtype | bfloat16 |
| MAX_GENERATION_INPUT_TOKENS | 4096（与其它模型对齐保证公平比较） |
| MAX_GENERATION_NEW_TOKENS | 1024 |

## 官方生成参数（来自 generation_config.json）

| 参数 | 值 |
|------|---|
| bos_token_id | 128000 (`<\|begin_of_text\|>`) |
| eos_token_id | 128001 (`<\|end_of_text\|>`) |
| temperature | 0.6 |
| top_p | 0.9 |
| top_k | 0（禁用） |
| do_sample | true（baseline）|

## Prompt 策略

**Prompt 内容直接复用现有 Qwen/Gemma summary-only prompts，内容一字不改。**
版本字符串加了 `llama3_` 前缀以区分模型来源：

- CNN/DailyMail：`llama3_cnn_dailymail_concise_summary_only_v1`
- Multi-News：`llama3_multi_news_concise_summary_only_v1`

> base 模型无 chat_template，`_render_prompt` 直接返回原始 prompt 文本（completion style）。
> `_use_stop_strings=True` 让 generate 循环遇到 "Summarize the following news article" 或
> "Summarize the following collection" 时主动停止，避免 base 模型续写下一个任务。

## 解码策略

| 模式 | 策略 |
|------|------|
| Baseline | Sampling（temperature=0.6，top_p=0.9） |
| CO（n>1） | Deterministic beam search（num_beams=8，num_return_sequences=8） |
| CO（n=1） | Greedy（temperature=0） |

`do_sample="auto"`：baseline 自动走 sampling，CO 自动走 beam search。

## 评估指标（全量，每次运行固定）

`rouge`、`bertscore`、`factcc`、`minicheck`、`alignscore`、`factgraph`、`factkb`

在 `cli/args.py` 末尾硬编码，运行时不可跳过。

## 快速启动

```bash
# Baseline CNN/DailyMail 全量（推荐走仓库根目录的包装脚本，已内置 HF_TOKEN 与 queue 机制）
bash run_llama_cnn_baseline_full_eval.sh

# 或直接调用 1_llama3_8b/run_baseline.sh（需自行 export HF_TOKEN）
HF_TOKEN=<你的token> bash 1_llama3_8b/run_baseline.sh

# Smoke test（2 个样本）
cd 1_llama3_8b && HF_TOKEN=<token> python run.py \
  --method baseline \
  --generator llama3_8b \
  --dataset cnn_dailymail \
  --num-samples 2 \
  --sample-mode head \
  --compute-dtype bf16

# Multi-News
DATASET=multi_news bash 1_llama3_8b/run_baseline.sh
```

## HuggingFace 认证

`meta-llama/Llama-3.1-8B` 是 gated repo，首次使用需：
1. 用账号访问 https://huggingface.co/meta-llama/Llama-3.1-8B 点 "Agree and access repository"
2. 等 Meta 审批通过（设置 → Gated Repositories 显示 "accepted"）
3. 创建 fine-grained token，勾选 "Read access to contents of all public gated repos you can access"
4. 通过环境变量注入：`export HF_TOKEN=hf_xxx`（仓库根目录的 `run_llama_cnn_baseline_full_eval.sh` 已内置）

## 目录结构

```
1_llama3_8b/
  run.py                   # CLI 入口（从 1_qwen3.5_9B 原样复制）
  run_baseline.sh          # baseline 快捷脚本
  core/
    config.py              # Llama-3 专属配置（新建）
    model_generation.py    # HF 推理后端（从 1_qwen3.5_9B 复制，仅改版本字符串）
    orchestration.py       # 实验主流程（从 1_qwen3.5_9B 原样复制）
    data.py / features.py  # 数据/特征工具（原样复制）
  cli/
    args.py                # CLI 参数解析（从 1_gemma_4_e4b 复制，改 generator 名）
  metrics/                 # 评估工具（原样复制）
  shared/                  # 共享工具（原样复制）
  opt_selectors/           # ILP/DPP/MMR 选择器（原样复制）
```
