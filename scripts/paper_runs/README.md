# Paper Run Scripts

`run_current_paper_rows.sh` is a sanitized release wrapper for the local rows
reported in the current paper table. It calls the top-level release runner and
streams every job through `scripts/run_live.sh`.

The original project also contains machine-specific queue scripts under
`<SOURCE_EXPERIMENT_ROOT>`. Those scripts are not copied verbatim because some
contain local absolute paths, queue assumptions, or credentials. The release
keeps the executable behavior through configurable wrappers instead.
