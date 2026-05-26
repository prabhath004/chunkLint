# ChunkLint

Static analysis for RAG chunks before they enter a vector database.

ChunkLint checks chunk files and in-memory Python chunk objects for structural
problems that usually show up later as bad retrieval, incomplete answers, or
expensive re-indexing work. It is intentionally simple: no LLM calls, no
embeddings, no eval dataset, and no vector database connection required.

The rules are deterministic heuristics. They are built to catch likely chunking
mistakes with low runtime cost, but they are not a substitute for a labeled
retrieval-quality benchmark.

## Why It Exists

A normal RAG pipeline often moves directly from splitting to embedding:

```python
docs = loader.load()
chunks = splitter.split_documents(docs)
vectorstore.add_documents(chunks)
```

If those chunks are malformed, missing context, duplicated, or split in the
middle of an important sentence, the vector database stores that damage. You
usually discover it much later when retrieval gives poor context to the model.

ChunkLint adds a quality gate between chunking and embedding:

```python
from chunklint.adapters.langchain import lint_documents

docs = loader.load()
chunks = splitter.split_documents(docs)

report = lint_documents(chunks)
if report.has_high_issues:
    report.print()
    raise RuntimeError("ChunkLint failed")

vectorstore.add_documents(chunks)
```

## What It Catches

ChunkLint focuses on obvious static chunk quality issues:

- Empty or whitespace-only chunks
- Missing stable chunk IDs
- Missing source metadata
- Missing heading, title, or section context
- Chunks that likely start mid-sentence
- Chunks that likely end mid-sentence
- Tiny chunks with little usable context
- Very large chunks that may mix topics
- Markdown table fragments without headers
- Unclosed markdown code fences
- Near-duplicate chunks
- Common PDF extraction noise

## What It Is Not

ChunkLint is not a RAG observability platform, an LLM judge, a retriever eval
tool, a vector database scanner, a PDF parser, or a chunk-size optimizer. It is
a fast static analyzer that catches preventable chunk problems before indexing.

## Install

From PyPI, once published:

```bash
pip install chunklint
```

For local development from this repository:

```bash
cd /Users/prabhathpalakurthi/Desktop/ChunkLint
python -m pip install -e .
```

Optional framework extras:

```bash
pip install "chunklint[langchain]"
pip install "chunklint[llamaindex]"
```

Developer tools:

```bash
python -m pip install -e ".[dev]"
```

## Quickstart

Use the included bad chunk fixture:

```bash
chunklint scan examples/bad_chunks.json
```

Fail CI when high-severity issues exist:

```bash
chunklint scan examples/bad_chunks.json --fail-on high
```

Write a JSON report:

```bash
chunklint scan examples/bad_chunks.json --format json --out report.json
```

If the console script is not on your PATH, run the module directly:

```bash
python -m chunklint.cli scan examples/bad_chunks.json
```

## CLI

### `scan`

Scans JSON or JSONL chunk exports.

```bash
chunklint scan chunks.json
chunklint scan chunks.jsonl
chunklint scan chunks.json --fail-on high
chunklint scan chunks.json --format json
chunklint scan chunks.json --format json --out report.json
chunklint scan chunks.json --config chunklint.yml
chunklint scan chunks.json --quiet
```

Exit codes:

- `0`: scan completed and did not fail the selected threshold
- `1`: lint threshold failed, such as `--fail-on high`
- `2`: invalid input or invalid config
- `3`: unexpected internal error

### `init`

Creates a default config file.

```bash
chunklint init
```

Create a config at a custom path:

```bash
chunklint init config/chunklint.yml
```

Overwrite an existing config:

```bash
chunklint init --force
```

### `rules`

Lists rule IDs, default severities, and whether each rule checks one chunk or
the full chunk set.

```bash
chunklint rules
```

More CLI detail is in [docs/cli.md](docs/cli.md).

## Python SDK

The generic SDK accepts dictionaries, `Chunk` models, and supported framework
objects.

```python
from chunklint import lint

chunks = [
    {
        "id": "chunk_1",
        "text": "Refund Policy. Customers can request refunds within 30 days.",
        "source": "refund_policy.md",
        "metadata": {"heading": "Refund Policy"},
    },
    {
        "id": "chunk_2",
        "text": "except enterprise customers may request refunds within 90 days.",
        "source": "refund_policy.md",
        "metadata": {"heading": "Refund Policy"},
    },
]

report = lint(chunks)

if report.has_high_issues:
    report.print()
    raise RuntimeError("ChunkLint failed")
```

The returned report includes counts and issue objects:

```python
print(report.chunks_scanned)
print(report.issues_found)
print(report.high, report.medium, report.low)
print(report.ok)
```

More SDK detail is in [docs/sdk.md](docs/sdk.md).

## LangChain

LangChain `Document` objects are mapped from `page_content` and `metadata`.

```python
from chunklint.adapters.langchain import export_documents, lint_documents

docs = loader.load()
chunks = splitter.split_documents(docs)

report = lint_documents(chunks)

if report.has_high_issues:
    report.print()
    raise RuntimeError("ChunkLint failed")

export_documents(chunks, "chunks.json")
vectorstore.add_documents(chunks)
```

## LlamaIndex

LlamaIndex nodes are mapped from `node.get_content()`, `node.node_id`,
`node.metadata`, and `node.ref_doc_id`.

```python
from chunklint.adapters.llamaindex import export_nodes, lint_nodes

nodes = parser.get_nodes_from_documents(documents)
report = lint_nodes(nodes)

if report.has_high_issues:
    report.print()
    raise RuntimeError("ChunkLint failed")

export_nodes(nodes, "chunks.json")
index = VectorStoreIndex(nodes)
```

## Input Format

JSON input should be an array of chunk objects:

```json
[
  {
    "id": "chunk_1",
    "text": "Refund Policy. Customers can request refunds within 30 days.",
    "source": "refund_policy.pdf",
    "metadata": {
      "page": 2,
      "heading": "Refund Policy"
    }
  }
]
```

JSONL input should have one chunk object per line:

```json
{"id":"chunk_1","text":"Refund Policy. Customers can request refunds within 30 days.","source":"refund_policy.pdf","metadata":{"page":2,"heading":"Refund Policy"}}
{"id":"chunk_2","text":"except enterprise customers may request refunds within 90 days.","source":"refund_policy.pdf","metadata":{"page":2,"heading":"Refund Policy"}}
```

Supported text keys for dictionary inputs include `text`, `page_content`, and
`content`. Source can be supplied as a top-level `source` or through metadata
keys such as `source`, `file_name`, `path`, or `document_id`.

## Config

ChunkLint automatically loads `chunklint.yml` or `chunklint.yaml` from the
current working directory. You can also pass a config explicitly:

```bash
chunklint scan chunks.json --config path/to/chunklint.yml
```

Example config:

```yaml
version: 1

thresholds:
  min_words: 30
  max_words: 700
  duplicate_similarity: 0.92
  max_line_break_ratio: 0.35

heading_keys:
  - heading
  - title
  - section
  - heading_path
  - document_title
  - file_name

rules:
  starts_mid_sentence:
    enabled: true
    severity: high
    connector_words:
      - except
      - however
      - therefore
      - because
      - although
      - which
      - that
      - and
      - but
      - or
      - also
      - then
    ignore_start_words:
      - iphone
      - ebay
      - npm
      - openai

  too_short:
    enabled: true
    severity: low

  near_duplicate:
    enabled: true
    severity: low
```

Full rule and config reference: [docs/rules.md](docs/rules.md).

## Rules

| Rule | Default | Scope | Purpose |
| --- | --- | --- | --- |
| `missing_text` | high | chunk | Flags empty chunks. |
| `missing_id` | medium | chunk | Flags chunks without stable IDs. |
| `missing_source` | medium | chunk | Flags chunks without traceable source metadata. |
| `missing_heading` | medium | chunk | Flags chunks without heading/title/section metadata. Page labels are not treated as headings. |
| `starts_mid_sentence` | high | chunk | Flags likely mid-sentence starts using continuation punctuation, configurable connector words, lowercase starts, and false-positive exclusions for headings, code, tables, and known product/tool names. |
| `ends_mid_sentence` | medium | chunk | Flags likely mid-sentence endings using missing punctuation, continuation punctuation, and trailing connector words while skipping headings, tables, code, URLs, and colon labels. |
| `too_short` | low | chunk | Flags chunks below `min_words`; raises to medium when heading context is missing. |
| `too_long` | medium | chunk | Flags chunks above `max_words`. |
| `broken_markdown_table` | high | chunk | Flags table fragments without markdown separator/header context. |
| `broken_code_block` | medium | chunk | Flags odd counts of triple-backtick fences. |
| `near_duplicate` | low | cross-chunk | Flags chunks above the duplicate similarity threshold. |
| `pdf_noise` | low | cross-chunk | Flags page labels, repeated headers/footers, hyphenation, and line-break artifacts. |

## Reports

Terminal output is designed for humans:

```text
ChunkLint Report

Chunks scanned: 3
Issues found: 6

High:   2
Medium: 2
Low:    2
```

JSON output is designed for CI, logs, or downstream tools:

```json
{
  "summary": {
    "chunks_scanned": 3,
    "issues_found": 6,
    "high": 2,
    "medium": 2,
    "low": 2
  },
  "issues": [
    {
      "chunk_id": "chunk_2",
      "source": "refund_policy.pdf",
      "rule_id": "starts_mid_sentence",
      "severity": "high",
      "reason": "Chunk starts with connector word \"except\".",
      "why_it_matters": "This chunk likely depends on a previous sentence and may lose the main rule.",
      "fix": "Use sentence-aware splitting or increase overlap.",
      "snippet": "except enterprise customers may request refunds within 90 days."
    }
  ]
}
```

## CI

Use ChunkLint as a pre-embedding quality gate:

```yaml
name: ChunkLint

on:
  pull_request:
    paths:
      - "docs/**"
      - "scripts/generate_chunks.py"
      - "chunklint.yml"

jobs:
  chunklint:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install chunklint

      - name: Generate chunks
        run: python scripts/generate_chunks.py

      - name: Run ChunkLint
        run: chunklint scan chunks.json --fail-on high
```

The same workflow is available at [examples/github_action.yml](examples/github_action.yml).

## Project Layout

```text
chunklint/
  cli.py              # Typer CLI commands
  config.py           # YAML config model and defaults
  engine.py           # Rule orchestration and report creation
  loader.py           # JSON/JSONL load and export helpers
  models.py           # Pydantic models for chunks, issues, reports
  normalizer.py       # Converts dicts/framework objects into Chunk models
  reporter.py         # Rich terminal output and JSON report serialization
  adapters/           # LangChain and LlamaIndex adapters
  rules/              # One file per rule family
  utils/              # Text, metadata, and severity helpers
docs/                 # User and contributor documentation
examples/             # Demo inputs and integration snippets
tests/                # Pytest coverage for CLI, loader, adapters, and rules
```

## Test Folder Guide

The `tests/` folder is the safety net for the first release:

| File | What it verifies |
| --- | --- |
| `tests/test_loader.py` | JSON array loading, JSONL loading, and chunk export behavior. |
| `tests/test_cli.py` | CLI exit codes, `--fail-on`, JSON report writing, and config initialization. |
| `tests/test_adapters.py` | LangChain and LlamaIndex adapter normalization, linting, and export helpers. |
| `tests/test_missing_rules.py` | `missing_text`, `missing_id`, `missing_source`, and `missing_heading`. |
| `tests/test_boundary_rules.py` | Mid-sentence start/end detection, stronger continuation signals, false-positive exclusions, and boundary-rule config options. |
| `tests/test_table_rule.py` | Broken markdown table detection and valid table pass-through. |
| `tests/test_code_rule.py` | Unclosed markdown code-fence detection. |
| `tests/test_duplicate_rule.py` | Near-duplicate detection across chunks. |
| `tests/test_pdf_noise_rule.py` | PDF page-label noise and repeated footer/header detection. |

More detail is in [docs/testing.md](docs/testing.md).

Run tests:

```bash
python -m pytest
```

Run linting when dev dependencies are installed:

```bash
python -m ruff check .
```

## Current Status

ChunkLint is an early v0.1.0 implementation. It already has the core SDK, CLI,
config, rule engine, framework adapters, examples, and tests. The next useful
steps are packaging polish, more real-world chunk fixtures, and integration
testing against actual LangChain and LlamaIndex objects.

## License

MIT. See [LICENSE](LICENSE).
