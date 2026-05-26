# Testing

ChunkLint uses pytest. The suite is intentionally small and focused on the
public behavior of the CLI, SDK, adapters, loader, and rules.

## Run Tests

```bash
python -m pytest
```

Install dev dependencies first when needed:

```bash
python -m pip install -e ".[dev]"
```

Run one file:

```bash
python -m pytest tests/test_cli.py
```

Run one test:

```bash
python -m pytest tests/test_cli.py::test_cli_scan_json_fails_on_high
```

## Test Folder

The `tests/` folder contains the automated checks for the current v0.1.0
surface area.

### `tests/test_loader.py`

Covers file input and export:

- JSON arrays are loaded into `Chunk` models.
- JSONL files are loaded one object per line.
- Metadata source values are normalized into `Chunk.source`.
- Export helpers write JSONL correctly.

### `tests/test_cli.py`

Covers user-facing command behavior:

- `chunklint scan ... --fail-on high --quiet` exits with code `1` when high
  issues exist.
- `chunklint scan ... --out report.json --quiet` writes a JSON report.
- `chunklint init <path>` creates a config file containing default rules.

### `tests/test_adapters.py`

Covers framework adapter boundaries without requiring the real framework
packages:

- Fake LangChain-like documents can be linted.
- Fake LangChain-like documents can be exported.
- Fake LlamaIndex-like nodes can be linted.
- Fake LlamaIndex-like nodes can be exported.

### `tests/test_missing_rules.py`

Covers metadata and identity rules:

- Empty text produces `missing_text` with high severity.
- Missing ID, source, and heading are reported.
- Valid source and heading metadata avoid false positives.

### `tests/test_boundary_rules.py`

Covers chunk boundary heuristics:

- Connector-word starts such as `except ...` trigger `starts_mid_sentence`.
- Continuation punctuation such as `, except ...` triggers `starts_mid_sentence`.
- Valid discourse starts such as `However, ...` are not flagged.
- Lowercase product/tool starts such as `iPhone ...` and `npm ...` are not flagged.
- Short lowercase heading lines are not flagged as sentence fragments.
- Chunks without sentence-ending punctuation trigger `ends_mid_sentence`.
- Continuation endings such as a trailing comma or trailing `and` trigger
  `ends_mid_sentence`.
- Colon-ended labels such as `Required documents:` are allowed.
- Markdown table starts are not incorrectly flagged as mid-sentence starts.
- Connector words and ignored start words can be customized through rule config.
- Adjacent chunk pairs can trigger `broken_chunk_boundary` when one chunk ends
  unfinished and the next starts as a continuation.

### `tests/test_table_rule.py`

Covers markdown table handling:

- Pipe-delimited table fragments without a separator row trigger
  `broken_markdown_table`.
- Proper markdown tables with a separator row pass that rule.

### `tests/test_code_rule.py`

Covers fenced code block handling:

- An odd number of triple-backtick fences triggers `broken_code_block`.

### `tests/test_duplicate_rule.py`

Covers cross-chunk duplicate detection:

- Similar chunks are compared with RapidFuzz and later duplicates are flagged as
  `near_duplicate`.

### `tests/test_pdf_noise_rule.py`

Covers PDF extraction artifacts:

- Page-label text triggers `pdf_noise`.
- Repeated header/footer-style lines across chunks trigger `pdf_noise`.
- Spaced PDF hyphenation such as `semi -structured` triggers `pdf_noise`.
- Repeated punctuation spacing such as `that , on one hand ,` triggers `pdf_noise`.

### `tests/test_reporter.py`

Covers report usability:

- Issue groups summarize repeated findings by rule.
- JSON output includes `groups` and `recommendations`.
- Recommendations are generated from dominant issue types.

## Generated Files

Do not commit generated runtime files:

- `__pycache__/`
- `.pytest_cache/`
- `.ruff_cache/`
- coverage outputs
- ad hoc scan reports such as `report.json`

The repository `.gitignore` already excludes Python caches and common build
artifacts. Generated reports should be kept out of commits unless they are
intentional fixtures.
