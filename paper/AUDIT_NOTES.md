# Paper Audit Notes

`Budget-constrained and faithful.tex` is the authoritative paper snapshot, but
it is not submission-ready. `zeyu.tex` is kept only as an older/reference draft.

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
  files, or from explicitly marked archived-summary rows when no full text
  result file exists.
- Do not use the Multi-News BART baseline result to fill the CNN/DM BART row;
  the dataset header and sample count identify it as Multi-News.
- Check `results/missing_results.csv` before presenting any row as fully
  supported by release artifacts.
- Do not report FactGraph as completed unless a final FactGraph run is present.
- Keep Llama Multi-News baseline marked pending until a final result file exists.
