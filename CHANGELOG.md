# Changelog

All notable changes to ChunkLint are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-26

First stable release. The CLI, Python SDK, framework adapters, rule set,
config schema, and JSON output (`schema_version: 1`) are now considered
public surface.

### Added
- `--fail-on-at-or-above {high|medium|low}` for threshold-style CI gating.
  Mutually exclusive with `--fail-on`.
- `--fail-on` now accepts a comma list (`--fail-on high,medium`) for
  multi-severity exact gating.
- `schema_version` field at the top of the JSON output, pinning the public
  output contract for downstream consumers.
- Elapsed scan time at the end of text reports.
- Colored severity badges in report and gate tables.
- Examples block in `scan --help`.
- Top offending chunks table in default and gate reports, ranking chunks
  by issue density.
- Quantified recommendations that show how many chunks each next-step
  affects (e.g., "affects 56 of 66 chunks, 85%").
- Sub-rule breakdown line for root causes that span multiple reasons
  (notably `pdf_noise`).
- GitHub Actions CI running ruff and pytest across Python 3.10, 3.11,
  and 3.12.
- Snapshot tests for the public JSON output schema (`test_json_schema.py`).
- Direct coverage for YAML config loading (`test_config.py`) and for
  loader edge cases such as malformed JSON, empty files, blank JSONL
  lines, and missing files.

### Changed
- `--fail-on` is now exact-severity rather than threshold-style. Use
  `--fail-on-at-or-above` for the prior threshold behavior.
- Gate output renders as structured tables (Gate result, Overall lint
  report, Root causes, Next steps) instead of free text.
- The `pdf_noise` rule reason now reads "Chunk contains a standalone
  page-number line." to reflect that detection is line-level.
- Project status bumped to Beta and project URLs added to `pyproject.toml`.

## [0.1.0] - initial development

Initial implementation: CLI, Python SDK, LangChain and LlamaIndex
adapters, 13 rules, YAML config, JSON/JSONL loader, and a Rich-based
text reporter.
