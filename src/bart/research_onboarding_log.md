# 科研记录：基于组合优化的抽象摘要生成

**项目启动日期**: 2026-02-07
**当前阶段**: 理论基础学习 (Onboarding)

## **第一周 (Week 1)**

## 1. 项目概况 (Project Overview)

**方向**: 组合优化用于抽象摘要生成 (Combinatorial Optimization for Abstractive Summarization)
**核心理念**: 将文本生成重新构建为一个离散决策问题 (Discrete Decision Problem)。
**目标**:

- 在预算和结构约束下，选择一组语义内容单元 (Semantic Content Units)，以最大化覆盖率 (Coverage)、多样性 (Diversity) 和 忠实度 (Faithfulness)。
- 将选定的内容转化为流畅的文本。
- 引入显式的可控性 (Explicit Controllability) 和理论保证 (Theoretical Guarantees)，如约束条件、近似界限、鲁棒性，以解决传统无约束序列生成的问题。

## 2. 初始任务 (Initial Assignment)

**目标**: 快速掌握理论基础，理解研究动机。暂不需要写代码。
**时间线**: 1-2周内完成阅读。
**会议安排**: 每周二下午 3:30 (Next Tuesday skipped)。

## 3. 阅读清单 (Reading List)

### A. 监督学习基础 (Basics of Supervised Learning)

建立机器学习的基本概念，理解模型训练流程和评估方法。

- [Supervised Machine Learning](https://www.geeksforgeeks.org/machine-learning/supervised-machine-learning/)
- [Train/Validation/Test Splits](https://www.geeksforgeeks.org/machine-learning/training-vs-testing-vs-validation-sets/)
- [Evaluation Metrics (Precision, Recall, F1)](https://www.geeksforgeeks.org/machine-learning/metrics-for-machine-learning-model/)

### B. NLP 与 Seq2Seq 模型入门 (Intro to NLP & Seq2Seq)

理解自然语言处理的核心架构，特别是序列到序列模型和注意力机制。

- [Step-by-Step with Transformers](https://arbisoft.com/blogs/step-by-step-with-transformers-from-seq2-seq-bottlenecks-to-cutting-edge-attention-mechanisms-in-nlp?)
- [Seq2Seq and Attention](https://lena-voita.github.io/nlp_course/seq2seq_and_attention.html)
- [Hugging Face LLM Course - Chapter 1](https://huggingface.co/learn/llm-course/chapter1/2)

### C. 核心论文 (Summarization Core)

了解当前领域的关键进展和具体方法。

- [arXiv:2310.09411 (Section 1 & 2.1)](https://arxiv.org/pdf/2310.09411)
  * *Focus*: Introduction & Background

## 4. 进度记录 (Progress Log)

### 第一周 (Week 1): 理论基础与阅读 (2026-02-07 ~ 2026-02-11)

- [X] **监督学习基础**: 复习了 Train/Val/Test split, Precision/Recall/F1 等概念。
- [X] **NLP 入门**: 学习了 Seq2Seq 架构和 Attention 机制。
- [X] **Transformer 基础**: 阅读了 Hugging Face Course Chapter 1，理解了 Transformer 的基本工作原理。
- [X] **核心论文阅读**: 阅读了 arXiv:2310.09411 的 Introduction 和 Background 部分，了解了将摘要生成视为离散优化问题的研究动机。

### 第二周 (Week 2): Hugging Face 实践入门 (2026-02-12 ~ )

#### [新任务]：Hugging Face 实践与文本生成模型构建

**邮件要求 (2026-02-12)**:

* **学习目标**:
  1. 阅读 Hugging Face LLM Course Chapter 3 (前三节)。
  2. 理解 Tokenization (分词) 原理。
  3. 理解如何加载 Pretrained Transformer 模型。
  4. 理解 Hugging Face API 文本生成流程。
  5. 理解 Transformer pipeline 的基本结构。
* **实践任务**:
  * 构建一个简单的文本生成模型 (使用 PyTorch + Transformers)。

#### 学习记录

- [X] **Hugging Face Course Chapter 3**:
  - 学习了数据处理 (Processing the data)。
  - 学习了模型微调 (Fine-tuning) 的基本流程。
  - 学习了 Text Generation 的 pipeline 和底层实现。
- [X] **核心概念笔记**:
  - **Pipeline API**: 用于快速推理的高层接口。
  - **Tokenizer**: 负责将文本转换为模型可读的 input_ids (处理 subword)。
  - **Model**: 加载预训练权重 (如 GPT-2)。
  - **Decoding**: 理解了 Greedy Search (确定性) 和 Sampling (随机性/创造性) 的区别。

### 第三周 (Week 3): 摘要模型实践与机器学习基础 (2026-02-17 ~ 2026-02-23)

#### [新任务]：摘要特征层级对比与基础算法学习

#### 学习记录

- [X] **摘要生成模型实践**:
  - 运行了 BART 模型对 Hugging Face 中的 **CNN/DailyMail** 数据集进行了抽象摘要提取。
  - 分别实现了 **词特征 (Token-level)** 和 **句子特征 (Sentence-level)** 两个版本的对比实验。
  - 针对算力瓶颈，首先在 **RunPod** 云端平台上完成了全量推理任务，随后在本地电脑上慢速运行与代码调试。
- [X] **机器学习算法基础**:
  - 学习并深入理解了**线性回归 (Linear Regression)** 的推导过程与代码实现。
  - 对**逻辑回归 (Logistic Regression)** 模型进行了学习。
  - 初步了解了 **XGBoost** 的核心原理。

### 第四周 (Week 4): 基于 BART 的零样本与组合优化探索 (2026-02-24 ~ )

#### 学习与实践记录

- [X] **BART 生成式摘要框架构建**:
  - 构建了纯 BART 生成式摘要的 PyTorch 框架，限制输出预算为 **3句话** (`Budget = 3`)。
  - 学习并使用了 **`pySBD`** 作为强大的句子拆分工具。
  - 将 Beam Search 的候选数设定为 3 (`num_beams=3, candidates=3`)，为后续优化预留操作空间。
- [X] **组合优化思想引入**:
  - 探索在上述 3 个 Beam Search 候选摘要中，如何利用**组合优化 (Combinatorial Optimization)** 方法挑选出最佳的一组输出摘要。
  - 对比研究了四到五种不同的优化 Candidates 方法，以期望获得更好的 Summary。
- [X] **摘要评估进阶**:
  - 认识到传统的 ROUGE 指标在评估摘要时的局限性。
  - 开始学习和调研新的自然语言处理评估体系与指标 (不再仅限于 ROUGE)，引入了 BERTScore、BARTScore、Faithfulness (NLI) 以及 REBEL 事实一致性测评。

### 第五周 (Week 5): 组合优化算法深挖与选句策略部署 (2026-03-03 ~ )

#### 学习与实践记录

- [ ] **组合优化深入剖析 (Combinatorial Optimization)**:
  - 意识到之前对组合优化的理解不够透彻，本周的核心任务是彻底搞懂底层逻辑。
  - 重点学习三种核心算法的数学原理及代码实现：**整数线性规划 (ILP)**、**行列式点过程 (DPP)**、**边际最大相关 (MMR)**。
  - 掌握硬约束 (Hard Constraints) 和软惩罚 (Soft Penalty) 的本质区别，以及求解器 (Solver) 如 CBC 的剪枝过程。
- [X] **部署 ROUGE-based 选句组合范式**:
  - 彻底完成了从 Token-level tokenize 到 **Sentence-level** 特征计算的认知转变。
  - 成功部署了 **Generate-then-Optimize** 范式代码：先用 BART 穷举生成候选池，再用 ROUGE-1/2 Recall 构建效用分数 (Utility)，用 ROUGE-L F1 构建冗余矩阵 (Redundancy)。
  - 利用数学优化器从候选池中完美挑选出低冗余、高信息的 Top-3 句子组合。
- [ ] **文献与源码双轨线**:
  - 继续研读与该框架强相关的 NLP 学术论文，搞清理论上限和前沿做法。
  - 对照自行跑通的 Beam-3 和 Beam-16 实验日志，逐行死磕代码逻辑，确保实现与论文公式100%对齐。

### 第六周 (Week 6): 指标导向的优化设计与前沿调研 (2026-03-16 ~ )

#### 学习与实践记录

- [ ] **系统框架自主设计与指标转向 (Framework Design & Metric Shift)**:
  - 导师会议沟通确认：当前生成框架已搭建完毕，后续全面进入自主设计阶段。
  - 核心痛点：现有基于概率生成的摘要模型，虽然 ROUGE 分数可能很高，但也非常容易产生事实幻觉 (Hallucination)。
  - 解决方案：对比 Baseline 时，将重点评估指标转向事实性评估。导师建议以 **FactCC** 作为核心评估指标，并探讨将其直接作为优化的目标函数。
- [ ] **分步目标函数实验 (Objective Function Experiments)**:
  - **阶段一 (单维指标基准)**：分别跑通两版基础模型，一版以传统的 ROUGE 为目标函数，另一版直接以 FactCC 作为目标函数。
  - **阶段二 (多维权重融合)**：在单维指标版本测试通过后，再考虑赋予不用指标相应的权重，组合作为更完善的目标函数。
- [ ] **细粒度指标下钻分析 (Granular Metric Analysis)**:
  - 在查看评估指标时，不能仅停留在综合的 F1 分数。
  - 必须深入分析 **Precision (精确率)** 和 **Recall (召回率)**，精确找出是哪一个特定指标在影响最终的 F1 表现。
- [ ] **前沿组合优化算法调研 (Advanced CO Algorithms)**:
  - 现有的组合优化 (CO) 方法相对老旧，需要重点调研文本生成/NLP 领域中近几年比较新的组合优化算法，作为后续替换和升级的原型。
- [ ] **预算约束控制探索 (Budget Settings)**:
  - 在完成目标函数设计和优化算法替换的前置实验后，将进一步探讨和设置预算约束 (Budget，例如句子数量、生成长度等)。
- [X] **FactCC 局限性与指标反思 (FactCC Limitations & Reflection)**:
  - **打分缺乏区分度**: BART beam search 生成的候选句子质量本身较好，FactCC 打分集中在 0.85-0.99 之间，差距极小 (0.01-0.04)。这导致：
    1. **作优化目标不合适**：细微差距可能是噪声，优化器在其中选择没有意义，解释了为何在 factcc_only 里 MMR/LNS/Submodular 结果完全一样。
    2. **作评估指标不合适**：微小分差无法衡量真正的 factuality 差异。FactCC 本质是二分类器，适合判断有无事实错误，不适合提供连续的区分度分数。
  - **Matched-metric Bias (指标过度拟合风险)**: 当 FactCC 同时被用作目标函数和评估指标时，只要算法朝其优化，分数必然畸高，高 FactCC 不等于真实事实性变好。
  - **代码实现的可靠性问题**:
    - 未经过官方管道，直接将 HF `manueldeprada/FactCC` 当作句对分类器取 `P(CORRECT)`，该途径不且未经验证，被证明不可靠 (Sanity check 发现明显错误的句子也能得到接近1.0的概率)。
    - 将句级分数取平均作为 summary-level 分数是一种不稳固的额外定义。
  - **受影响范围辨识**: 
    - 凡依赖旧 FactCC 作为目标函数的评估结果 (FactCC only, FactCC+Redundancy, MBR+FactCC, Pareto含FactCC等) 都需谨慎重新审视。
    - 四套算法 family 设计本身、ROUGE 实验以及指标无关的结构部分保持成立。
  - **目前稳妥的观察结论**:
    - budget3 baseline 的公平性逻辑正确，Precision < Recall 证明系统偏向 coverage 逻辑依然成立。
    - 作为独立的 Factuality 指标，**未来应更坚实依赖 AlignScore 和 NLI**。当前这部分结果显示：相较于裸跑 Baseline(raw) 事实性有上升，但对于限定了三句话的公平 Baseline(b3) 尚未出现显著超越。

### 第七周 (Week 7): Baseline 异常排查与前沿方法复现横评 (2026-03-24 ~ )

#### 学习与实践记录

- [ ] **Baseline 结果异常排查**:
  - 本周在运行 Baseline 时，发现本地跑出的结果与 Hugging Face 官方发布的结果存在显著差异（差很大）。
  - 目前高度怀疑是代码实现过程（如微调参数、推理配置或评估脚本）中存在 Bug，需要立刻逐行排查逻辑，以确保基准线数据的可靠性。
- [ ] **前沿方法论文阅读与复现**:
  - 查阅教授刚发送的更多关于摘要生成和事实性（Factuality）优化的相关论文。
  - 需要在我们的框架内去复现这些论文中提到的前沿方法，作为比对对象。
- [ ] **事实性横向对比测评 (Factuality Benchmarking)**:
  - 将我们提出的组合优化方法与上述复现出来的方法进行同款对比。
  - 核心验证诉求：观察我们的方法在事实准确性（Fact）和事实一致性上，是否能确凿地处于全面优势或优于他人。

### 第八周 (Week 8): Hugging Face Baseline 对齐结论与实验口径固定 (2026-03-26)

#### 学习与实践记录

- [X] **生成路径已与 Hugging Face 官方 `generate()` 对齐**:
  - 本地 `bart/shared/beam_search.py` 已改为直接调用 `BartForConditionalGeneration.generate(...)`。
  - 在同一篇 CNN/DailyMail 样本上，当前代码输出与直接调用官方 `model.generate(...)` 的输出逐字一致。
  - 当前使用的核心生成参数与 `facebook/bart-large-cnn` 的 `generation_config.json` 对齐:
    - `num_beams=4`
    - `max_length=142`
    - `min_length=56`
    - `length_penalty=2.0`
    - `no_repeat_ngram_size=3`
    - `forced_bos_token_id=0`

- [X] **主要差距已定位为评测口径差异，而不是明显实现错误**:
  - `beam4 + baseline_raw + test[:500] + HF ROUGE`:
    - `ROUGE-1 35.01`
    - `ROUGE-2 14.65`
    - `ROUGE-L 25.11`
    - `ROUGE-Lsum 31.94`
  - `beam4 + baseline_raw + train[:500] + HF ROUGE`:
    - `ROUGE-1 40.45`
    - `ROUGE-2 18.52`
    - `ROUGE-L 29.08`
    - `ROUGE-Lsum 38.04`
  - Hugging Face model card 页面显示的 legacy/self-reported 指标为:
    - `ROUGE-1 42.95`
    - `ROUGE-2 20.82`
    - `ROUGE-L 30.62`
    - `ROUGE-Lsum 40.04`
  - 当前判断: 之前最大的偏差来自 `test` 与 `train` 的 split 差异；在 `train[:500]` 上结果已经明显接近官方页面。

- [X] **当前固定的实验口径**:
  - `beam=3`:
    - `baseline_raw` = top-1 完整输出
    - `baseline3` = top-1 前 3 句
  - `beam=4`:
    - 只保留 `baseline_raw`，作为 Hugging Face reproduction baseline
  - 所有组合优化方法统一建立在 `beam=3` 候选生成之上，不再允许 `beam=4` 优化实验。

- [X] **评测口径补充**:
  - 正式实验默认使用 Hugging Face `evaluate` 的 ROUGE。
  - 为了快速做官方对齐排查，已新增 `--rouge-only-eval` 开关，只跑生成和 ROUGE，跳过 BERTScore / BARTScore / FactCC / MiniCheck / AlignScore。
  - `ROUGE-Lsum` 评测已按句子换行口径处理，更接近官方 summarization 示例。

- [X] **当前可接受的基线解释**:
  - `beam3 baseline_raw`: 项目主 baseline
  - `beam3 baseline3`: 预算为 3 句的公平 baseline
  - `beam4 baseline_raw`: Hugging Face reproduction baseline

- [X] **后续实验原则**:
  - 若未来继续逼近 Hugging Face model card 的最终数字，优先考虑增加样本量或跑 full train。
  - 当前阶段不再继续怀疑 baseline 生成实现，后续应把重点放回组合优化方法的对齐和横向比较。

### 第九周 (Week 9): 当前代码口径统一、结果汇总核对与汇报准备 (2026-04-01)

#### 学习与实践记录

- [X] **当前主干实验口径已统一到 MiniCheck，而不是旧的 FactCC 版本**:
  - `bart/shared/config.py` 当前四套 single-objective family 为:
    - `ROUGE only`
    - `ROUGE + Redundancy`
    - `MiniCheck only`
    - `MiniCheck + Redundancy`
  - 当前 `MBR` 与 `Pareto` 都不再属于上述四套 family，而是独立的 summary-level 方法。
  - 当前 `LNS` 的定位已明确为四套 family 内的搜索 / 求解方法，而不是新的 objective family。

- [X] **三种组合优化方法的当前代码定位已梳理清楚**:
  - `MBR`: 摘要级 `consensus + MiniCheck` 决策规则，当前权重为 `0.3 * consensus + 0.7 * MiniCheck`，已从旧的 FactCC 表述切换到 MiniCheck 口径。
  - `Pareto`: 摘要级多目标优化，同时考虑 `Coverage / MiniCheck / Redundancy`，先取 non-dominated front，再按 `MiniCheck > Coverage > lower Redundancy` 做 tie-break。
  - `LNS`: 使用 `top-k utility initialization + destroy-repair + small ILP repair`，在固定 objective family 下做 matheuristic 对照。

- [X] **项目内部结果汇总 CSV 已完成内容核对**:
  - `bart/results/summary_metrics_beam3_hfrouge.csv` 当前共 `25` 行:
    - `24` 行 test 结果
    - `1` 行 `baseline_raw` train reproduction 结果
  - 已使用 `scripts/build_summary_metrics_csv.py` 做无序核对，`25/25` 个 key 全匹配，未发现任何数值差异。
  - 之前 `--check-existing` 失败的主要原因已定位为 CSV 行顺序与脚本稳定排序不一致，而不是指标解析错误。

- [X] **unified_eval 结果口径与复现完成度已梳理**:
  - `bart/results/unified_eval/unified_comparison.csv` 当前共 `32` 个方法条目:
    - `24` 个项目内 `500-sample` 可跑方法
    - `8` 个外部论文复现条目
  - 当前总体状态为:
    - `26 runnable`
    - `6 partial`
  - unified 报告当前以 `MiniCheck` 作为 primary FACT metric，这与当前主干代码一致。

- [X] **外部论文复现当前仍以 partial / smoke 为主，尚不能做严格 paper-to-paper 结论**:
  - `lexisem = 1 sample`
  - `simcls = 2 samples`
  - `brio_ctr = 2 samples`
  - `submodular_budgeted = 1 sample`
  - `summa_reranker`、`factedit`、`consum` 仍缺关键 prerequisite
  - `submodular_acl2011` 虽有 `500` 样本结果，但与原论文 `DUC` 设定不直接可比

- [X] **当前老师汇报的最稳妥口径已固定**:
  - 内部方法已经可以在统一的 `beam-3 + budget=3 + HF ROUGE + 同套 factuality metrics` 口径下做横向比较。
  - `baseline3` 仍是最强公平 ROUGE baseline。
  - `pareto_summary_pareto` 是当前项目内 factuality 最强的方法。
  - `mbr_summary_mbr` 可视为比 Pareto 更保 ROUGE 的 summary-level 折中点。
  - 外部 baseline 复现仍处于 partial / smoke 阶段，暂时不能做严格的 paper-to-paper 定量结论。

### 第十/十一周 (Week 10-11): 权重搜索确立、效率考量与论文筹备 (2026-04-08 ~ 2026-04-15)

#### 学习与实践记录

- [ ] **停止权重过度搜索与方法精简**:
  - **导师反馈**：权重搜索告一段落，不要一直纠结于寻找最优权重，现有的几套极值或调优权重足以说明问题。
  - **聚焦方法**：选择最终表现最好、具有代表性的 **4 种候选方法** 来作为主战力。

- [ ] **时间效率与 Baseline 比较 (Runtime Efficiency)**:
  - **导师反馈**：做实验不能只比效果，必须考虑运行时间和效率。
  - **核心任务**：把所选方法的耗时情况与 baseline 进行严谨的横向对比，证明我们的组合优化不会在时间上带来不可接受的极大劣势。

- [ ] **实验配置与评估系统升级**:
  - **参数放大**：生成阶段的 `Beam Size` 已确定改为 **10**，提供更多的候选句子池。
  - **新评估方式**：加上老师新给的**三种评估方式**，补全评估体系的多元视角。

- [ ] **论文配图制作与案例展示 (Paper Workflow & Case Study)**:
  - **绘制流程图**：开始学习使用画图工具（如 OmniGraffle/draw.io/TikZ 等）制作论文中的 Pipeline 流程图。
  - **图表结合**：需要将流程图结合**一个具体的 Case** 加上 **数据表格 (Data Table)**，具象化地向读者展示“我们的方法是如何对这几个候选句子进行打分、权衡并最终输出结论的”。
