# 文本摘要评估指标完全指南

> 本文档覆盖项目中使用的全部 6 类评估指标，从原理、公式、直觉理解到代码实现逐一讲解。

---

## 目录

1. [ROUGE — 词重叠指标](#1-rouge--词重叠指标)
2. [METEOR — 改进的词匹配指标](#2-meteor--改进的词匹配指标)
3. [BERTScore — 语义相似度指标](#3-bertscore--语义相似度指标)
4. [BARTScore — 生成概率指标](#4-bartscore--生成概率指标)
5. [Faithfulness (NLI) — 忠实度指标](#5-faithfulness-nli--忠实度指标)
6. [REBEL Triplet Factual Consistency — 事实三元组一致性](#6-rebel-triplet-factual-consistency--事实三元组一致性)
7. [指标之间的关系与选择建议](#7-指标之间的关系与选择建议)

---

## 1. ROUGE — 词重叠指标

### 1.1 是什么

ROUGE（Recall-Oriented Understudy for Gisting Evaluation）是最经典的摘要评估指标，由 Chin-Yew Lin 在 2004 年提出。核心思想很简单：**数一数生成摘要和参考摘要之间有多少词/短语是重叠的**。

### 1.2 三个变体

#### ROUGE-1：Unigram 重叠

逐个**单词**比较。

```
参考摘要: "The cat sat on the mat"
生成摘要: "The cat is on the mat"

重叠的 unigram: {The, cat, on, the, mat} = 5 个
参考摘要总 unigram 数: 6
生成摘要总 unigram 数: 6
```

#### ROUGE-2：Bigram 重叠

逐个**连续两词组合**比较。

```
参考摘要 bigrams: {The cat, cat sat, sat on, on the, the mat}
生成摘要 bigrams: {The cat, cat is, is on, on the, the mat}

重叠 bigrams: {The cat, on the, the mat} = 3 个
```

ROUGE-2 比 ROUGE-1 更严格，因为它要求连续两个词都匹配，更能反映**语序和短语级别**的相似性。

#### ROUGE-L：最长公共子序列 (LCS)

找两个句子的**最长公共子序列**（不要求连续，但要求顺序一致）。

```
参考摘要: "The cat sat on the mat"
生成摘要: "The cat is on the mat"

LCS: "The cat on the mat"（长度 5）
```

ROUGE-L 的优势在于不要求严格连续匹配，更灵活地捕捉结构相似性。

### 1.3 P / R / F1 三个值

每个 ROUGE 变体都会计算三个值：

```
                  重叠词数
Precision (P) = ──────────────
                生成摘要总词数

                重叠词数
Recall (R)    = ──────────────
                参考摘要总词数

                    2 × P × R
F1            = ──────────────
                    P + R
```

**直觉理解**：
- **Recall（召回率）**：参考摘要中的内容，生成摘要覆盖了多少？→ "该说的说了没？"
- **Precision（精确率）**：生成摘要中的内容，有多少是参考摘要也提到的？→ "说的都对吗？"
- **F1**：两者的调和平均，综合评判

> 例如你的 Baseline 结果：rouge1 P=24.93% R=46.93% F1=31.35%
> - R 远高于 P → 生成的摘要比参考摘要长，覆盖了很多参考内容（高 R），但也说了很多参考里没有的话（低 P）

### 1.4 优缺点

| 优点 | 缺点 |
|------|------|
| 简单直观，计算快 | 只看词面重叠，"dog"和"canine"算不匹配 |
| 学术界标准指标，便于对比 | 不考虑语义，改述（paraphrase）会被惩罚 |
| 有 P/R/F1 多角度评估 | 对摘要长度敏感（长摘要天然高 R） |

### 1.5 实际使用中的参考范围

在 CNN/DailyMail 数据集上，SOTA 模型的典型范围：
- ROUGE-1 F1: 40-45%
- ROUGE-2 F1: 18-22%
- ROUGE-L F1: 35-40%

你的实验中 F1 偏低（~31%），因为你是从 beam 候选中选 3 句拼接，而非端到端生成。

---

## 2. METEOR — 改进的词匹配指标

### 2.1 是什么

METEOR（Metric for Evaluation of Translation with Explicit ORdering）最初为机器翻译设计，后广泛用于摘要评估。它是 ROUGE 的**增强版**，解决了 ROUGE 的几个核心痛点。

### 2.2 四层匹配机制

METEOR 不只做精确匹配，而是按优先级依次尝试四种匹配：

```
第 1 层：Exact Match（精确匹配）
  "cat" ↔ "cat"  ✓

第 2 层：Stem Match（词干匹配）
  "running" ↔ "ran"  ✓（都归约为 run）

第 3 层：Synonym Match（同义词匹配，基于 WordNet）
  "dog" ↔ "canine"  ✓

第 4 层：Paraphrase Match（短语改述匹配）
  "in control of" ↔ "dominating"  ✓
```

这意味着 METEOR 能识别 ROUGE 无法识别的语义等价表达。

### 2.3 计算过程

**Step 1: 对齐（Alignment）**

找到生成摘要和参考摘要之间的最佳一对一词匹配。

**Step 2: 计算 P 和 R**

```
              匹配词数
P = ─────────────────────
    生成摘要 unigram 总数

              匹配词数
R = ─────────────────────
    参考摘要 unigram 总数
```

**Step 3: 调和平均（偏向 Recall）**

```
           10 × P × R
F_mean = ───────────────
          R + 9 × P
```

注意系数是 9:1 偏向 Recall，因为摘要评估中覆盖度更重要。

**Step 4: 惩罚碎片化（Fragmentation Penalty）**

这是 METEOR 的独特设计：如果匹配的词在原文中不是连续的，说明语序被打乱了，需要惩罚。

```
            chunk 数
Penalty = 0.5 × (──────────)^3
            匹配词数

METEOR = F_mean × (1 - Penalty)
```

其中 **chunk** 是连续匹配的最大段数。chunk 越少（匹配越连续），惩罚越小。

```
例子：
参考: "The president of the United States"
生成: "The United States president"

匹配词: The, president, United, States (4个)
chunks: [The] [United States] [president] = 3 个 chunk
Penalty = 0.5 × (3/4)^3 = 0.211
```

### 2.4 与 ROUGE 的关键区别

| 特性 | ROUGE | METEOR |
|------|-------|--------|
| 匹配方式 | 仅精确匹配 | 精确+词干+同义词+改述 |
| 语序考虑 | ROUGE-L 通过 LCS 间接考虑 | 通过碎片化惩罚直接考虑 |
| 召回偏好 | 名字里就有 Recall-Oriented | 9:1 偏向 Recall |
| 与人类判断相关性 | 中等 | 较高（这是它的设计目标） |

### 2.5 参考范围

CNN/DailyMail 上 SOTA 模型 METEOR 一般在 30-40% 之间。你的 Baseline 33.96% 在合理范围内。

---

## 3. BERTScore — 语义相似度指标

### 3.1 是什么

BERTScore（2020, Zhang et al.）利用预训练语言模型（如 RoBERTa）的上下文嵌入来计算语义相似度。它解决了 ROUGE 的核心问题：**同义词和改述应该得到匹配**。

### 3.2 核心思想

```
传统方法:  "dog" vs "canine" → 不匹配（字面不同）
BERTScore: "dog" vs "canine" → 高度匹配（语义向量接近）
```

### 3.3 计算步骤

**Step 1: 获取上下文嵌入**

将参考摘要和生成摘要分别输入预训练模型（你用的是 roberta-large），得到每个 token 的上下文向量。

```
参考摘要 tokens: [x₁, x₂, ..., xₘ]  →  向量: [x⃗₁, x⃗₂, ..., x⃗ₘ]
生成摘要 tokens: [y₁, y₂, ..., yₙ]  →  向量: [y⃗₁, y⃗₂, ..., y⃗ₙ]
```

注意这是**上下文**嵌入，不是静态词向量。同一个词在不同句子中的向量不同。

**Step 2: 计算 token 间余弦相似度矩阵**

```
sim(xᵢ, yⱼ) = cos(x⃗ᵢ, y⃗ⱼ) = (x⃗ᵢ · y⃗ⱼ) / (‖x⃗ᵢ‖ × ‖y⃗ⱼ‖)
```

得到一个 m×n 的相似度矩阵。

**Step 3: 贪心最大匹配**

```
                1
Recall    = ─── × Σᵢ max_j sim(xᵢ, yⱼ)     对参考的每个 token，找生成中最相似的
                m

                1
Precision = ─── × Σⱼ max_i sim(xᵢ, yⱼ)     对生成的每个 token，找参考中最相似的
                n

                    2 × P × R
F1        = ────────────────
                    P + R
```

**直觉**：
- R：参考摘要里的每个词，在生成摘要中都能找到语义相近的词吗？
- P：生成摘要里的每个词，在参考摘要中都有语义对应吗？

### 3.4 IDF 加权（可选）

BERTScore 可以使用 IDF（逆文档频率）加权，让稀有词（通常更重要）获得更高权重：

```
                Σᵢ idf(xᵢ) × max_j sim(xᵢ, yⱼ)
R_idf   = ──────────────────────────────────────
                      Σᵢ idf(xᵢ)
```

### 3.5 数值范围与解读

BERTScore 的范围理论上是 [-1, 1]，但实际上通常在 [0.8, 0.95] 之间，区分度较小。

```
你的实验结果:
  Baseline:    F1 = 86.83%
  DP-Knapsack: F1 = 86.85%   ← 最高
  Submodular:  F1 = 83.36%   ← 最低

差距仅 ~3.5%，但在 BERTScore 的尺度上这已经是显著差异。
```

### 3.6 为什么用 roberta-large？

不同的底层模型会影响 BERTScore 的灵敏度：
- `roberta-large`：最常用，效果好，与人类判断相关性高
- `bert-base`：速度快但区分度较低
- `deberta-xlarge-mnli`：更新更准，但计算量大

### 3.7 优缺点

| 优点 | 缺点 |
|------|------|
| 能识别同义词和改述 | 数值范围窄，差异需仔细看 |
| 上下文感知（同一词不同语境向量不同） | 依赖底层模型质量 |
| 与人类判断相关性高 | 计算成本比 ROUGE 高很多 |
| 支持多语言 | 对事实错误不敏感（"猫吃鱼"vs"鱼吃猫"可能分数相近） |

---

## 4. BARTScore — 生成概率指标

### 4.1 是什么

BARTScore（2021, Yuan et al.）用 BART 模型的**生成概率**来评估文本质量。核心思想：如果一个好的生成模型认为"从 A 生成 B"的概率很高，那说明 B 是 A 的好摘要。

### 4.2 核心公式

```
BARTScore(A → B) = (1/|B|) × Σₜ log P(bₜ | b<t, A)
```

即：把 A 作为 encoder 输入，让 BART decoder 逐 token 生成 B，取所有 token 的对数概率的平均值。

**直觉**：如果 BART 觉得"给定 A，B 是一个很自然的输出"，那分数就高。

### 4.3 三个方向

你的实验中测了三个方向，每个方向衡量不同的质量维度：

#### ref → hyp（参考 → 生成）

```
BARTScore(reference → hypothesis)
```

含义：给定参考摘要，BART 认为生成摘要有多"合理"？

衡量维度：**语义覆盖 / 信息保留**

如果生成摘要包含了参考摘要的关键信息，那从参考摘要"生成"出生成摘要的概率就高。

```
你的结果: Baseline = -3.04, Submodular = -2.41（最高）
Submodular 最高是因为它倾向于选择更长、更详细的句子
（但这并不一定是好事，见 hyp→ref 的另一面）
```

#### hyp → ref（生成 → 参考）

```
BARTScore(hypothesis → reference)
```

含义：给定生成摘要，BART 认为参考摘要有多"合理"？

衡量维度：**精确性 / 无冗余**

如果生成摘要简洁且信息精准，那从生成摘要到参考摘要的转换也应该容易。

```
你的结果: Baseline = -3.63（最高）, Submodular = -4.11（最低）
Submodular 最低说明它生成了太多参考摘要里没有的冗余内容
```

#### src → hyp（原文 → 生成）

```
BARTScore(source → hypothesis)
```

含义：给定原始文章，BART 认为生成摘要有多"合理"？

衡量维度：**忠实度 / 流畅度**

这不需要参考摘要！直接衡量生成摘要是否像原文的一个好摘要。

```
你的结果: MMR = -0.55（最高）, CP-SAT = -0.93（最低）
MMR 选出的句子从原文角度看最"自然"
```

### 4.4 数值解读

BARTScore 的值是**对数概率的平均值**，因此：
- 总是负数（概率 < 1，取 log 后为负）
- **越接近 0 越好**（概率越高）
- 典型范围: [-5, 0]

```
-0.5  → 很好（平均每个 token 的概率 ≈ e^(-0.5) ≈ 60%）
-3.0  → 中等（平均每个 token 的概率 ≈ e^(-3.0) ≈ 5%）
-5.0  → 较差（平均每个 token 的概率 ≈ e^(-5.0) ≈ 0.7%）
```

### 4.5 与其他指标的本质区别

```
ROUGE / METEOR  →  比较"表面词汇"重叠
BERTScore       →  比较"语义向量"相似度
BARTScore       →  用"生成概率"衡量质量（完全不同的范式！）
```

BARTScore 的独特优势：
1. **方向性**：可以分别评估覆盖度、精确性、忠实度
2. **无参考评估**：src→hyp 方向不需要参考摘要
3. **全局语义**：不是 token 级别匹配，而是整体生成概率

### 4.6 优缺点

| 优点 | 缺点 |
|------|------|
| 三个方向提供多维度评估 | 依赖 BART 模型本身的质量 |
| src→hyp 可以做无参考评估 | 计算量大（需要完整的 encoder-decoder 前向传播） |
| 与人类判断相关性最高之一 | 对 BART 没见过的领域/语言效果差 |
| 能捕捉流畅度和连贯性 | 数值绝对大小难以直观理解 |

---

## 5. Faithfulness (NLI) — 忠实度指标

### 5.1 是什么

Faithfulness 衡量的是生成摘要对原始文章的**忠实程度**——生成的内容是不是原文真正表达的意思，有没有"编造"信息。

这里使用的是基于 **NLI（Natural Language Inference，自然语言推理）** 的方法。

### 5.2 NLI 基础知识

NLI 任务是判断两个句子之间的逻辑关系：

```
前提 (Premise):    "A man is playing guitar on stage."
假设 (Hypothesis): "A musician is performing."         → Entailment（蕴含）
假设 (Hypothesis): "A man is sleeping."                → Contradiction（矛盾）
假设 (Hypothesis): "The man is wearing a red shirt."   → Neutral（中立）
```

### 5.3 用 NLI 评估忠实度的原理

```
前提 = 原始文章（source）
假设 = 生成摘要的每个句子

如果 NLI 模型判断"蕴含"（Entailment）→ 这个句子忠实于原文
如果 NLI 模型判断"矛盾"或"中立"   → 这个句子可能是编造的
```

### 5.4 计算过程

```
对于生成摘要中的每个句子 sᵢ:
  score_i = P(Entailment | source, sᵢ)    # NLI 模型输出蕴含的概率

                Σ score_i
Faithfulness = ───────────
                    N
```

你用的模型是 `bart-large-mnli`，这是在 MultiNLI 数据集上微调的 BART。

### 5.5 直觉理解

```
原文: "The company reported revenue of $5 billion in Q3 2024."

生成句子 A: "The company earned $5 billion in the third quarter."
  → Entailment (高概率) → 忠实 ✓

生成句子 B: "The company's revenue exceeded $10 billion."
  → Contradiction → 不忠实 ✗（数字被夸大）

生成句子 C: "The CEO expressed optimism about future growth."
  → Neutral → 可能不忠实 ✗（原文没说这个）
```

### 5.6 你的实验结果解读

```
DP-Knapsack: 85.20%  ← 最忠实
Baseline:    84.79%
ILP:         78.98%
CP-SAT:      78.03%
MMR:         76.15%
DPP:         73.15%
Submodular:  69.94%  ← 最不忠实
```

Submodular 只有 69.94%——看它的样本输出就知道，它经常选出重复的、不相关的句子，甚至包含 URL 和无关内容。

### 5.7 局限性

| 局限 | 说明 |
|------|------|
| 长文本截断 | NLI 模型输入长度有限（通常 512/1024 tokens），长原文会被截断 |
| 只判断蕴含，不判断重要性 | 一个忠实但完全不重要的句子也会得高分 |
| 依赖 NLI 模型质量 | NLI 模型本身可能犯错 |
| 粒度粗 | 只能判断句子级别，无法定位具体哪个词/事实出错 |

---

## 6. REBEL Triplet Factual Consistency — 事实三元组一致性

### 6.1 是什么

这是最"硬核"的事实性评估方法。它不看词汇重叠，不看语义向量，而是**提取结构化的事实三元组**，然后比较生成摘要和参考摘要中的事实是否一致。

### 6.2 什么是事实三元组

事实三元组 = (主语 Subject, 关系 Relation, 宾语 Object)

```
句子: "Barack Obama was born in Hawaii."
三元组: (Barack Obama, born in, Hawaii)

句子: "Apple acquired Beats Electronics for $3 billion."
三元组: (Apple, acquired, Beats Electronics)
        (Apple, acquired for, $3 billion)
```

### 6.3 REBEL 模型

REBEL（Relation Extraction By End-to-end Language generation）是 Babelscape 开发的关系提取模型（基于 BART），能从自然语言文本中自动提取三元组。

```
输入: "Elon Musk founded SpaceX in 2002."
REBEL 输出: (Elon Musk, founder, SpaceX)
            (SpaceX, inception, 2002)
```

### 6.4 计算过程

```
Step 1: 用 REBEL 从参考摘要提取三元组集合 T_ref
Step 2: 用 REBEL 从生成摘要提取三元组集合 T_hyp
Step 3: 计算重叠

              |T_ref ∩ T_hyp|
Precision = ─────────────────     生成的三元组中，多少在参考里也有？
                |T_hyp|

              |T_ref ∩ T_hyp|
Recall    = ─────────────────     参考的三元组中，多少被生成摘要覆盖了？
                |T_ref|

                  2 × P × R
F1        = ─────────────────
                  P + R
```

### 6.5 匹配方式

三元组匹配通常不是严格的字符串精确匹配，而可能使用：

```
严格匹配:  (Obama, born in, Hawaii) vs (Obama, born in, Hawaii)  → ✓
模糊匹配:  (Obama, born in, Hawaii) vs (Barack Obama, birthplace, Hawaii)  → 可能 ✓
```

具体取决于实现方式（你的实现可能用的是精确匹配或基于相似度的匹配）。

### 6.6 你的实验结果解读

```
ILP:         P=28.67%  R=11.39%  F1=15.05%  ← 最高
Baseline:    P=19.00%  R=8.95%   F1=11.17%
MMR:         P=21.67%  R=7.02%   F1=9.82%
CP-SAT:      P=17.00%  R=5.74%   F1=8.15%
Submodular:  P=16.67%  R=5.30%   F1=7.64%
DP-Knapsack: P=10.00%  R=3.90%   F1=5.04%
DPP:         P=11.00%  R=3.47%   F1=4.90%
```

整体分数很低（F1 最高才 15%），这是正常的：
1. REBEL 提取的三元组可能不完整
2. 相同事实的表述方式很多，精确匹配很难命中
3. 生成摘要和参考摘要本身关注的事实角度可能不同

ILP 最高说明它选出的句子在**结构化事实**层面与参考摘要最为接近。

### 6.7 与 Faithfulness (NLI) 的区别

```
Faithfulness (NLI):
  问: "生成摘要的内容能从原文推导出来吗？"  → 衡量对原文的忠实度
  对比对象: source vs hypothesis

REBEL Triplet:
  问: "生成摘要的事实和参考摘要的事实一致吗？" → 衡量与参考答案的事实重合度
  对比对象: reference vs hypothesis
```

两者衡量的维度完全不同：
- NLI：忠于原文（不编造）
- REBEL：与参考答案的事实一致（选对了事实）

### 6.8 优缺点

| 优点 | 缺点 |
|------|------|
| 从事实结构层面评估，最接近"对错"判断 | 高度依赖 REBEL 模型的三元组提取质量 |
| 不受表述方式影响（理论上） | 提取不完整时分数偏低 |
| 可以精确到每个事实进行分析 | 无法处理隐含事实和推理 |
| 提供可解释的错误分析 | 匹配策略影响很大（精确 vs 模糊） |

---

## 7. 指标之间的关系与选择建议

### 7.1 评估维度总览

```
                        需要参考摘要?     评估什么?
                        ─────────────    ──────────────────
ROUGE                      是            词面重叠（表面相似度）
METEOR                     是            增强词匹配（含同义词+语序）
BERTScore                  是            语义相似度（向量空间）
BARTScore (ref↔hyp)        是            生成概率（信息保留/精确性）
BARTScore (src→hyp)        否 ★          生成概率（忠实度/流畅度）
Faithfulness (NLI)         否 ★          蕴含关系（忠实度）
REBEL Triplet              是            事实三元组重合度
```

### 7.2 从"表面"到"深层"的层次

```
浅层 ←──────────────────────────────→ 深层

ROUGE-1    ROUGE-2    METEOR    BERTScore    BARTScore    NLI    REBEL
(单词)     (双词)    (同义词)   (语义向量)   (生成概率)  (逻辑) (事实)
```

越往右越"深层"，与人类判断的相关性通常越高，但计算成本也越大。

### 7.3 每个指标最擅长发现的问题

| 指标 | 最擅长发现 |
|------|-----------|
| ROUGE | 摘要是否覆盖了关键词 |
| METEOR | 摘要是否用不同的词表达了相同的意思 |
| BERTScore | 摘要是否在语义上与参考接近 |
| BARTScore | 摘要是否流畅、是否像一个"自然的摘要" |
| Faithfulness | 摘要是否编造了原文没有的信息 |
| REBEL | 摘要是否包含了正确的事实 |

### 7.4 你的实验中各指标告诉我们什么

以 **DP-Knapsack** 为例（综合表现最好）：

```
ROUGE-1 F1 = 31.02%     → 词面覆盖接近 Baseline
BERTScore  = 86.85%     → 语义上最接近参考摘要
Faithfulness = 85.20%   → 最不容易编造信息
REBEL F1   = 5.04%      → 但事实三元组匹配很低

→ 结论: DP 选出的句子语义正确、忠实于原文，但和参考摘要关注的"具体事实点"不同
```

以 **Submodular** 为例（综合最差）：

```
ROUGE-1 F1 = 19.40%     → 词面覆盖很低
BERTScore  = 83.36%     → 语义上偏离参考
Faithfulness = 69.94%   → 30% 的内容可能是不忠实的
从样本看: 大量重复句子 → 冗余问题严重
```

### 7.5 论文写作中的使用建议

```
必报指标:    ROUGE-1/2/L (学术惯例)、BERTScore
推荐加上:    BARTScore (展示多维度分析)、Faithfulness (展示忠实度)
锦上添花:    METEOR、REBEL (展示全面性)
```

### 7.6 一句话记住每个指标

```
ROUGE:          "你们俩用了多少一样的词？"
METEOR:         "一样的词 + 一样意思的词 + 语序对不对？"
BERTScore:      "AI 觉得你们说的意思有多像？"
BARTScore:      "AI 觉得这个摘要有多'自然'？"
Faithfulness:   "摘要有没有瞎编？"
REBEL Triplet:  "摘要说的事实和答案对得上吗？"
```

---

## 附录：代码速查

### ROUGE
```python
from rouge_score import rouge_scorer
scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
scores = scorer.score(reference, hypothesis)
```

### BERTScore
```python
from bert_score import score
P, R, F1 = score([hypothesis], [reference], lang="en", model_type="roberta-large")
```

### BARTScore
```python
from BARTScore import BARTScorer
scorer = BARTScorer(checkpoint='facebook/bart-large-cnn')
score = scorer.score(srcs=[source], tgts=[hypothesis])  # src→hyp
```

### Faithfulness (NLI)
```python
from transformers import pipeline
nli = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
result = nli(hypothesis, candidate_labels=["entailment", "contradiction", "neutral"])
```

### METEOR
```python
import nltk
score = nltk.translate.meteor_score.meteor_score([reference.split()], hypothesis.split())
```

### REBEL
```python
from transformers import pipeline
rebel = pipeline("text2text-generation", model="Babelscape/rebel-large")
triplets = rebel(text)  # 提取三元组
```
