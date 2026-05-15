# Paper Audit Notes

`zeyu.tex` is the authoritative paper snapshot for this release.

Required fixes before ACL/ARR submission:

- Replace the placeholder ACL template abstract with the real abstract.
- Remove the ACL template material that appears after the first Conclusion
  section.
- Add the missing `latex/Pipeline.png` file or revise the figure reference.
- Add `custom.bib` or update the bibliography command.
- Anonymize author names, affiliations, emails, and supplementary metadata if
  submitting for anonymous review.
- Keep Multi-News and CNN/DM Llama CO table cells blank unless final result
  files are selected and the paper is intentionally updated.
- Do not report FactGraph unless a completed FactGraph evaluation is added.

Release-side handling:

- `paper/zeyu.tex` is copied verbatim from the source experiment workspace so
  paper issues remain auditable.
- Filled local CNN/DM rows are backed by compact result files in `results/raw/`.
- External reference rows are separated into
  `results/external_reference_metrics.csv`.
- Non-reported result artifacts are kept under `results/auxiliary/`.
