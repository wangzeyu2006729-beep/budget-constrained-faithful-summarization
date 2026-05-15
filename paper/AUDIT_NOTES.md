# Paper Audit Notes

`Budget-constrained and faithful.tex` is the authoritative paper snapshot, but
it is not submission-ready. The older `zeyu.tex` draft is intentionally excluded
from the release package to avoid conflicting paper sources.

Required fixes before ACL/ARR submission:

- Add the missing bibliography file referenced as `custom.bib`, or update the
  bibliography command.
- Anonymize author names, affiliations, and supplemental material if submitting
  for anonymous review.
- Fill result table blanks only from completed `results/raw/**/*_results.txt`
  files, or from explicitly marked archived-summary rows when no full text
  result file exists.
- Do not use the Multi-News BART baseline result to fill the CNN/DM BART row;
  the dataset header and sample count identify it as Multi-News.
- Check `results/missing_results.csv` before presenting any row as fully
  supported by release artifacts.
- Do not report FactGraph as completed unless a final FactGraph run is present.
- Llama Multi-News baseline is no longer pending; the final result file is
  copied into `results/raw/`, but its MiniCheck cell remains unavailable.
- Keep Llama Multi-News CO selector rows pending until final selector result
  files exist.

Fixed during release audit:

- Replaced the ACL-template abstract with a code-aligned release abstract.
- Removed trailing ACL template material after the paper draft.
- Replaced the missing `latex/Pipeline.png` include with an inline text pipeline.
- Reworded the method section so it no longer claims a general monotone
  submodular guarantee or exact DPP inference.
- Removed the non-authoritative `paper/zeyu.tex` draft from the release copy.
