# Paper Audit Notes

`zeyu.tex` is copied as the authoritative paper snapshot, but it is not
submission-ready.

Required fixes before ACL/ARR submission:

- Replace the placeholder ACL-template abstract with the real abstract.
- Remove all ACL template text that begins after the paper's first
  `\section{Conclusion}`.
- Add the missing figure asset referenced as `latex/Pipeline.png`, or update the
  figure path.
- Add the missing bibliography file referenced as `custom.bib`, or update the
  bibliography command.
- Anonymize author names, affiliations, and supplemental material if submitting
  for anonymous review.
- Fill result table blanks only from completed `results/raw/**/*_results.txt`
  files.
- Do not report FactGraph as completed unless a final FactGraph run is present.
- Keep Llama Multi-News baseline marked pending until a final result file exists.
