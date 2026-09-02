# Contributing

Create changes on a branch, run `python -m pytest`, and run
`python -m scripts.check_release` before opening a pull request. Do not attach
or commit Tribal/OLC-controlled records, precise governed locations, access
credentials, or locally cached downloads.

Changes to governance language require review by the OST/OLC-designated
authority. Technical contributors may propose wording in an issue, but should
not represent a draft as approved policy.

Before committing notebooks, run `python -m scripts.prepare_notebooks` to remove
execution outputs and machine-specific state while preserving narrative and code.

For scientific changes, document the source version, CRS and vertical datum,
units, resolution, validation evidence, uncertainty, and effect on published
artifacts. New claims about data gaps or institutional causes require a cited,
reproducible evidence record.
