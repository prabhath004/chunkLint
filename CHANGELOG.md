# Changelog

All notable changes to ChunkLint are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

While ChunkLint is on `0.x`, minor versions may introduce breaking changes.
The public JSON output is independently versioned via `schema_version`.

## [0.1.0] - 2026-05-26

First public release on PyPI.

### CLI

- `chunklint scan` for JSON / JSONL chunk files with text and JSON output modes.
- `chunklint init` writes a default `chunklint.yml` config.
- `chunklint rules` lists supported rules, default severities, and scope.
- Two mutually exclusive gate flags:
  - `--fail-on` — exact severity. Accepts a comma list (`--fail-on high,medium`).
  - `--fail-on-at-or-above` — threshold style (`medium` blocks medium and high).
- Exit codes: `0` clean, `1` gate failed, `2` invalid input/config, `3` internal error.
- `--quiet`, `--verbose`, `--raw`, `--max-issues`, `--examples-per-rule`, `--out`, `--config`.

### Python SDK and adapters

- `from chunklint import lint, Chunk, Issue, LintReport` public surface.
- Accepts dictionaries, `Chunk` models, and framework objects.
- LangChain adapter: `lint_documents`, `export_documents`.
- LlamaIndex adapter: `lint_nodes`, `export_nodes`.

### Rules

Thirteen deterministic rules across boundaries, metadata, sizing, structure,
duplication, and PDF artifacts. Severity is configurable per rule, and any
rule can be disabled via `chunklint.yml`.

### Reports

- Text reports group rules into developer-facing root causes with
  recommended fixes.
- Top offending chunks table ranks chunks by issue density.
- Recommendations quantify reach (e.g., `affects 56 of 66 chunks, 85%`).
- Sub-rule breakdown line under each root cause when multiple distinct
  reasons fire.
- Colored severity badges and elapsed scan time in text output.
- JSON output carries `schema_version: 1` for downstream consumers.

### Project infrastructure

- GitHub Actions CI runs ruff and pytest across Python 3.10, 3.11, and 3.12
  on every push and pull request to `main`.
- 97 tests covering loader, CLI, config, adapters, rules, reporter, and
  the public JSON output contract.
