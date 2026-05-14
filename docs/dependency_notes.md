# Dependency Notes

## Python Environment

The release code was copied from the working experiment environment. The current
server environment already has a project virtualenv at:

```bash
/home/zeyu/projects/NLP_ilp_dpp_mmr_experiment/.venv/bin/python
```

For a fresh environment, install the baseline dependencies listed in
`requirements.txt`. Some metric packages and checkpoints are large and may need
manual installation or local paths.

```bash
cd /home/zeyu/projects/NLP_acl_repro_release

python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## External Assets

The source code resolves external assets through `NLM_ASSETS_DIR` or
`src/.nlm_assets.json`. This release includes:

```json
{
  "assets_root": "/mnt/stu/zeyu/NLM_data/assets/NLM_generatesummary"
}
```

That asset root currently contains FactCC, MiniCheck, AlignScore, FactGraph, and
checkpoint folders. If you run elsewhere, set:

```bash
export NLM_ASSETS_DIR=/path/to/assets/root
```

Expected optional subdirectories include:

- `MiniCheck-main`
- `minicheck_ckpts`
- `AlignScore-main`
- `alignscore_ckpt`
- `factCC-master`
- `FACTGRAPH-main`

## DPP Dependency

The original experiment tree vendored `DPPy-master`, but the actual release DPP
selector uses its own deterministic greedy log-determinant routine and does not
call `dppy`. The copied release code removes that unused import so DPP runs do
not require vendoring `DPPy-master`.

## BERTScore Dependency

The original tree vendored `bert_score-master`. The release code first imports
the installed `bert_score` package from the Python environment and only falls
back to an external `bert_score-master` asset if the package is missing.

## Metric Caveats

- ROUGE uses Hugging Face `evaluate` by default with NLTK sentence splitting for
  ROUGE-Lsum.
- BERTScore uses `roberta-large`.
- MiniCheck is used both as a selector signal and an evaluation diagnostic.
- FactGraph appears in the code as an extra metric, but copied results report it
  as unavailable. The paper should not claim FactGraph as a reported metric
  unless a completed FactGraph evaluation is added.
