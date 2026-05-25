# ChunkLint Technical PRD

## Product Name

**ChunkLint**

## One-Line Pitch

**ChunkLint is ESLint for RAG chunks — a fast, no-LLM static analyzer that catches broken, context-missing, duplicate, or malformed chunks before they enter a vector database.**

---

## 1. Product Summary

ChunkLint is an open-source Python SDK and CLI that checks RAG chunks before they are embedded into a vector database.

It helps developers catch obvious chunk quality problems early, such as:

- Missing source metadata
- Missing heading/title context
- Chunks starting mid-sentence
- Chunks ending mid-sentence
- Broken markdown tables
- Broken code blocks
- Tiny useless chunks
- Huge mixed-topic chunks
- Duplicate or near-duplicate chunks
- PDF header/footer noise

The goal is simple:

> Stop bad chunks before they enter Pinecone, Chroma, Qdrant, Weaviate, Supabase pgvector, or any other vector database.

---

## 2. Problem

A normal RAG pipeline looks like this:

```text
PDF / docs
   ↓
Loader extracts text
   ↓
Splitter creates chunks
   ↓
Chunks are embedded
   ↓
Vector DB stores embeddings
   ↓
Retriever pulls chunks
   ↓
LLM answers
```

The problem is that developers usually send chunks directly from the splitter into the vector database.

Example:

```python
docs = loader.load()
chunks = splitter.split_documents(docs)
vectorstore.add_documents(chunks)
```

If those chunks are bad, the vector DB stores bad context.

Later, this causes:

- Bad retrieval
- Missing context
- Incomplete answers
- More hallucinations
- Expensive debugging
- Expensive re-chunking
- Expensive re-embedding

Most tools focus on tracing, evaluation, or retrieval scoring after the system fails.

ChunkLint focuses on an earlier step:

> Are these chunks structurally bad before embedding?

---

## 3. Target Users

### Primary Users

- AI engineers building RAG apps
- Backend engineers maintaining vector DB pipelines
- Developers using LangChain or LlamaIndex
- Teams building support-doc chatbots
- Teams building internal knowledge assistants
- Open-source maintainers building docs Q&A bots

### Secondary Users

- DevRel teams
- Documentation teams
- AI infrastructure teams
- LLM observability teams

---

## 4. Core Product Goal

ChunkLint should give developers a fast quality gate before embedding chunks.

Python SDK flow:

```python
docs = loader.load()
chunks = splitter.split_documents(docs)

report = chunklint.lint(chunks)

if report.has_high_issues:
    report.print()
    raise RuntimeError("Bad chunks found")

vectorstore.add_documents(chunks)
```

CLI flow:

```bash
chunklint scan chunks.json --fail-on high
```

---

## 5. Why Python

ChunkLint should be built in **Python**.

### Why Python is better than Go for v1

Python is the best choice because most RAG pipelines are already Python-based.

The ecosystem includes:

- LangChain
- LlamaIndex
- Chroma
- Qdrant
- Pinecone clients
- Weaviate clients
- Supabase pgvector tooling
- PyPDF / PDF loaders
- sentence-transformers
- tiktoken
- pandas
- scikit-learn

Go is good for fast standalone CLIs, but Python gives better access to the RAG and NLP ecosystem.

### Final Stack

```text
Language: Python
CLI: Typer
Terminal UI: Rich
Validation: Pydantic
Config: PyYAML
Duplicate detection: RapidFuzz
Testing: pytest
Packaging: pyproject.toml + pip/uv
```

---

## 6. What ChunkLint Is

ChunkLint is:

- A static analyzer for RAG chunks
- A CI quality gate for RAG pipelines
- A Python SDK for checking chunks in code
- A CLI for checking exported chunk files
- A lightweight developer tool before vector DB indexing

---

## 7. What ChunkLint Is Not

ChunkLint is not:

- A full RAG observability platform
- A LangSmith/Langfuse replacement
- A chunk-size optimizer
- A hallucination detector
- An LLM judge
- A PDF parser first
- A vector database
- A retrieval benchmark

Correct positioning:

> ChunkLint catches obvious chunk quality issues before indexing.

---

## 8. Normal RAG Pipeline

A typical RAG pipeline works like this:

```text
1. User has documents
   PDF, Markdown, Word, HTML, Notion, etc.

2. Loader reads the documents
   Example: PyPDFLoader reads a PDF.

3. Splitter creates chunks
   The document is split into smaller text pieces.

4. Chunks stay in memory
   Usually as Python objects, not JSON files.

5. Embedding model converts chunks into vectors

6. Vector DB stores those vectors
   Pinecone, Chroma, Qdrant, Supabase, Weaviate, etc.

7. User asks a question

8. Retriever searches vector DB and returns relevant chunks

9. LLM answers using those chunks
```

Flow:

```text
Docs/PDFs
   ↓
Loader
   ↓
Text splitter / chunker
   ↓
Chunks in memory
   ↓
Embeddings
   ↓
Vector DB
   ↓
Retriever
   ↓
LLM answer
```

---

## 9. Where ChunkLint Fits

ChunkLint goes between chunking and embedding.

```text
Docs/PDFs
   ↓
Loader
   ↓
Text splitter / chunker
   ↓
Chunks in memory
   ↓
ChunkLint checks chunks
   ↓
If chunks are good → embed them
If chunks are bad → show issues
   ↓
Vector DB
```

Final pipeline:

```text
PDF/docs → loader → chunker → ChunkLint → embeddings → vector DB → retriever → LLM
```

---

## 10. JSON Clarification

JSON is optional.

In a normal RAG pipeline, chunks are usually created in memory as Python objects.

Example:

```python
chunks = splitter.split_documents(docs)
```

Developers usually do not automatically create a `chunks.json` file.

They often directly do:

```python
vectorstore.add_documents(chunks)
```

ChunkLint should support both flows:

### Option 1: Python SDK

Best for real RAG pipelines:

```python
from chunklint import lint

chunks = splitter.split_documents(docs)

report = lint(chunks)

if report.has_high_issues:
    report.print()
else:
    vectorstore.add_documents(chunks)
```

### Option 2: CLI With JSON

Best for CI/debugging:

```bash
chunklint scan chunks.json --fail-on high
```

The JSON file is only a simple format for storing chunks.

Example:

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
  },
  {
    "id": "chunk_2",
    "text": "except enterprise customers may request refunds within 90 days.",
    "source": "refund_policy.pdf",
    "metadata": {
      "page": 2,
      "heading": "Refund Policy"
    }
  }
]
```

The user should not manually write this JSON.

ChunkLint should provide exporters:

```python
from chunklint.adapters.langchain import export_documents

export_documents(chunks, "chunks.json")
```

---

## 11. Core Use Cases

### Use Case 1: LangChain Pipeline Check

Current flow:

```python
docs = loader.load()
chunks = splitter.split_documents(docs)
vectorstore.add_documents(chunks)
```

ChunkLint flow:

```python
docs = loader.load()
chunks = splitter.split_documents(docs)

from chunklint.adapters.langchain import lint_documents

report = lint_documents(chunks)

if report.has_high_issues:
    report.print()
    raise RuntimeError("ChunkLint failed")

vectorstore.add_documents(chunks)
```

---

### Use Case 2: LlamaIndex Pipeline Check

```python
from chunklint.adapters.llamaindex import lint_nodes

nodes = parser.get_nodes_from_documents(documents)

report = lint_nodes(nodes)

if report.has_high_issues:
    report.print()
else:
    index = VectorStoreIndex(nodes)
```

---

### Use Case 3: CI Check Before Re-Indexing

A team has docs in GitHub. Every docs PR regenerates chunks.

```bash
python scripts/generate_chunks.py
chunklint scan chunks.json --fail-on high
```

If a docs change creates broken chunks, CI fails before the chunks are embedded.

---

### Use Case 4: Debugging Exported Chunks

A developer exports chunks from a custom pipeline:

```json
[
  {
    "id": "chunk_12",
    "text": "except enterprise customers may request refunds within 90 days.",
    "source": "refund_policy.pdf",
    "metadata": {
      "page": 2,
      "heading": "Refund Policy"
    }
  }
]
```

They run:

```bash
chunklint scan chunks.json
```

Output:

```text
HIGH starts_mid_sentence chunk_12
Reason: Chunk starts with connector word "except".
Fix: Use sentence-aware splitting or increase overlap.
```

---

## 12. Supported Inputs

### v1 SDK Inputs

Support:

- `list[dict]`
- `list[Chunk]`
- LangChain `Document` objects
- LlamaIndex `TextNode` / `BaseNode` objects

### v1 CLI Inputs

Support:

- JSON array
- JSONL

Example JSONL:

```json
{"id":"chunk_1","text":"Refund Policy. Customers can request refunds within 30 days.","source":"refund_policy.pdf","metadata":{"page":2,"heading":"Refund Policy"}}
{"id":"chunk_2","text":"except enterprise customers may request refunds within 90 days.","source":"refund_policy.pdf","metadata":{"page":2,"heading":"Refund Policy"}}
```

---

## 13. MVP Feature List

### Must Have

- Python SDK
- CLI
- JSON/JSONL loader
- LangChain adapter
- LlamaIndex adapter
- Static lint rules
- Terminal report
- JSON report export
- Config file
- CI fail mode
- Unit tests

### Should Have

- PDF-specific noise checks based on chunk text/metadata
- Markdown table/code block checks
- Near-duplicate detection
- GitHub Actions example
- Example bad chunk dataset

### Not v1

- No full PDF parsing
- No OCR
- No LLM calls
- No embeddings
- No retrieval eval
- No dashboard
- No vector DB direct scan

---

## 14. Integrations

## 14.1 LangChain Integration

LangChain uses `Document` objects with:

- `page_content`
- `metadata`

ChunkLint should convert each LangChain `Document` into internal `Chunk`.

### API

```python
from chunklint.adapters.langchain import lint_documents, export_documents

report = lint_documents(chunks)

export_documents(chunks, "chunks.json")
```

### Internal Mapping

```text
LangChain Document.page_content → Chunk.text
LangChain Document.metadata["source"] → Chunk.source
LangChain Document.metadata → Chunk.metadata
Document.id if available → Chunk.id
```

### Example

```python
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from chunklint.adapters.langchain import lint_documents

loader = PyPDFLoader("refund_policy.pdf")
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100
)

chunks = splitter.split_documents(docs)

report = lint_documents(chunks)

if report.has_high_issues:
    report.print()
    raise RuntimeError("ChunkLint failed")

vectorstore = Chroma(
    collection_name="policies",
    embedding_function=OpenAIEmbeddings()
)

vectorstore.add_documents(chunks)
```

---

## 14.2 LlamaIndex Integration

LlamaIndex uses `Documents` and `Nodes`.

ChunkLint should support nodes before they are inserted into indexes.

### API

```python
from chunklint.adapters.llamaindex import lint_nodes, export_nodes

report = lint_nodes(nodes)

export_nodes(nodes, "chunks.json")
```

### Internal Mapping

```text
node.get_content() → Chunk.text
node.node_id → Chunk.id
node.metadata → Chunk.metadata
node.ref_doc_id → Chunk.source if source missing
```

### Example

```python
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter

from chunklint.adapters.llamaindex import lint_nodes

documents = SimpleDirectoryReader("./docs").load_data()

parser = SentenceSplitter(
    chunk_size=800,
    chunk_overlap=100
)

nodes = parser.get_nodes_from_documents(documents)

report = lint_nodes(nodes)

if report.has_high_issues:
    report.print()
    raise RuntimeError("ChunkLint failed")

index = VectorStoreIndex(nodes)
```

---

## 14.3 Chroma Integration

ChunkLint v1 should not directly connect to Chroma.

Instead, it checks chunks before they are added.

```python
report = lint_documents(chunks)

if report.ok:
    chroma.add_documents(chunks)
```

Future v2:

```bash
chunklint scan-chroma --collection policies
```

---

## 14.4 Qdrant Integration

ChunkLint v1 should check documents before calling:

```python
QdrantVectorStore.from_documents(...)
```

or before:

```python
vectorstore.add_documents(chunks)
```

Future v2 can add direct Qdrant collection scan.

---

## 14.5 Generic Custom Pipeline Integration

Support plain dictionaries:

```python
from chunklint import lint

chunks = [
    {
        "id": "chunk_1",
        "text": "Refund Policy. Refunds are allowed within 30 days.",
        "source": "refund_policy.md",
        "metadata": {"heading": "Refund Policy"}
    }
]

report = lint(chunks)
```

---

## 15. Rule System

ChunkLint should use a modular rule engine.

### Rule Interface

```python
from abc import ABC, abstractmethod
from chunklint.models import Chunk, Issue, LintContext

class Rule(ABC):
    id: str
    default_severity: str

    @abstractmethod
    def check(self, chunk: Chunk, context: LintContext) -> list[Issue]:
        pass
```

### Cross-Chunk Rule Interface

```python
class CrossChunkRule(ABC):
    id: str
    default_severity: str

    @abstractmethod
    def check_all(self, chunks: list[Chunk], context: LintContext) -> list[Issue]:
        pass
```

---

## 16. MVP Lint Rules

## Rule 1: `missing_text`

Flags empty chunks.

Severity: high.

Detection:

```text
Text is empty, null, or whitespace only.
```

---

## Rule 2: `missing_id`

Flags chunks with no stable ID.

Severity: medium.

Why it matters:

```text
Without stable chunk IDs, debugging and deduping are harder.
```

Fix:

```text
Generate deterministic IDs using source + index + content hash.
```

---

## Rule 3: `missing_source`

Flags chunks with no source file/document/page reference.

Severity: medium.

Why it matters:

```text
If this chunk causes a bad answer, developer cannot trace it back.
```

---

## Rule 4: `missing_heading`

Flags chunks with no heading/title/section metadata.

Severity: medium.

Accept metadata keys:

```text
heading
title
section
heading_path
document_title
file_name
page_label
```

---

## Rule 5: `starts_mid_sentence`

Flags chunks that likely start mid-sentence.

Severity: high.

Heuristics:

```text
Starts with connector words:
except, however, therefore, because, although, which, that, and, but, or, also, then

or starts with lowercase letter
unless it is code/table/list content
```

---

## Rule 6: `ends_mid_sentence`

Flags chunks likely ending mid-sentence.

Severity: medium.

Heuristics:

```text
Does not end with ., !, ?, ), ], }, `, "
Ignore table rows, code blocks, URLs, bullets
```

---

## Rule 7: `too_short`

Flags tiny chunks.

Default:

```yaml
min_words: 30
```

Severity: low by default, medium if no heading metadata.

---

## Rule 8: `too_long`

Flags very long chunks.

Default:

```yaml
max_words: 700
```

Severity: medium.

---

## Rule 9: `broken_markdown_table`

Flags table fragments without headers.

Severity: high.

Detect:

```text
Chunk has multiple lines with |
but no markdown separator row like |---|---|
```

---

## Rule 10: `broken_code_block`

Flags unclosed markdown code fences.

Severity: medium.

Detect:

```text
Odd number of triple backticks
```

---

## Rule 11: `near_duplicate`

Flags chunks with high similarity.

Severity: low.

Default threshold:

```yaml
duplicate_similarity: 0.92
```

Use RapidFuzz for v1.

---

## Rule 12: `pdf_noise`

Flags common PDF extraction artifacts.

Severity: low/medium.

Detect:

- Repeated `Page X`
- Confidential footer repeated
- Standalone page numbers
- Weird hyphenation
- Too many line breaks
- Headers/footers repeated across many chunks

This rule needs cross-chunk context because headers/footers repeat across chunks.

---

## 17. Config File

Default config: `chunklint.yml`

```yaml
version: 1

thresholds:
  min_words: 30
  max_words: 700
  duplicate_similarity: 0.92
  max_line_break_ratio: 0.35

required_metadata:
  - source

heading_keys:
  - heading
  - title
  - section
  - heading_path
  - document_title
  - file_name

rules:
  missing_text:
    enabled: true
    severity: high

  missing_id:
    enabled: true
    severity: medium

  missing_source:
    enabled: true
    severity: medium

  missing_heading:
    enabled: true
    severity: medium

  starts_mid_sentence:
    enabled: true
    severity: high

  ends_mid_sentence:
    enabled: true
    severity: medium

  too_short:
    enabled: true
    severity: low

  too_long:
    enabled: true
    severity: medium

  broken_markdown_table:
    enabled: true
    severity: high

  broken_code_block:
    enabled: true
    severity: medium

  near_duplicate:
    enabled: true
    severity: low

  pdf_noise:
    enabled: true
    severity: low
```

---

## 18. CLI Commands

### `scan`

Main command.

```bash
chunklint scan chunks.json
```

Options:

```bash
chunklint scan chunks.json --format json
chunklint scan chunks.json --out report.json
chunklint scan chunks.json --fail-on high
chunklint scan chunks.json --config chunklint.yml
chunklint scan chunks.json --quiet
```

---

### `init`

Creates default config.

```bash
chunklint init
```

Output:

```text
Created chunklint.yml
```

---

### `rules`

Lists supported rules.

```bash
chunklint rules
```

---

## 19. Python SDK API

### Generic API

```python
from chunklint import lint

report = lint(chunks)

if report.has_high_issues:
    report.print()
```

---

### LangChain API

```python
from chunklint.adapters.langchain import lint_documents, export_documents

report = lint_documents(chunks)
export_documents(chunks, "chunks.json")
```

---

### LlamaIndex API

```python
from chunklint.adapters.llamaindex import lint_nodes, export_nodes

report = lint_nodes(nodes)
export_nodes(nodes, "chunks.json")
```

---

## 20. Data Models

### `Chunk`

```python
from pydantic import BaseModel, Field
from typing import Any

class Chunk(BaseModel):
    id: str | None = None
    text: str
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
```

---

### `Issue`

```python
class Issue(BaseModel):
    chunk_id: str | None
    source: str | None
    rule_id: str
    severity: str
    reason: str
    why_it_matters: str
    fix: str
    snippet: str | None = None
```

---

### `LintReport`

```python
class LintReport(BaseModel):
    chunks_scanned: int
    issues_found: int
    high: int
    medium: int
    low: int
    issues: list[Issue]

    @property
    def has_high_issues(self) -> bool:
        return self.high > 0

    @property
    def ok(self) -> bool:
        return self.issues_found == 0
```

---

## 21. Internal Architecture

```text
chunklint/
  pyproject.toml
  README.md
  LICENSE
  examples/
    bad_chunks.json
    langchain_example.py
    llamaindex_example.py
    github_action.yml

  chunklint/
    __init__.py
    cli.py
    config.py
    models.py
    loader.py
    engine.py
    reporter.py
    normalizer.py

    adapters/
      __init__.py
      langchain.py
      llamaindex.py

    rules/
      __init__.py
      base.py
      missing_text.py
      missing_id.py
      missing_source.py
      missing_heading.py
      boundary.py
      size.py
      markdown_table.py
      code_block.py
      duplicate.py
      pdf_noise.py

    utils/
      text.py
      metadata.py
      severity.py

  tests/
    test_loader.py
    test_langchain_adapter.py
    test_llamaindex_adapter.py
    test_missing_rules.py
    test_boundary_rules.py
    test_table_rule.py
    test_code_rule.py
    test_duplicate_rule.py
```

---

## 22. Dependencies

`pyproject.toml`

```toml
[project]
name = "chunklint"
version = "0.1.0"
description = "A static analyzer for RAG chunks"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
  "typer>=0.12.0",
  "rich>=13.0.0",
  "pydantic>=2.0.0",
  "pyyaml>=6.0.0",
  "rapidfuzz>=3.0.0"
]

[project.optional-dependencies]
langchain = [
  "langchain-core",
  "langchain-community"
]
llamaindex = [
  "llama-index-core"
]
dev = [
  "pytest",
  "ruff",
  "mypy"
]

[project.scripts]
chunklint = "chunklint.cli:app"
```

Install options:

```bash
pip install chunklint
pip install "chunklint[langchain]"
pip install "chunklint[llamaindex]"
```

---

## 23. Reporting

### Terminal Report

```text
ChunkLint Report
────────────────────────────────────────

Chunks scanned: 128
Issues found: 19

High:   4
Medium: 9
Low:    6

Top issues:
- starts_mid_sentence: 3
- missing_heading: 7
- broken_markdown_table: 1
- near_duplicate: 5
- too_short: 3

HIGH  starts_mid_sentence
Chunk: refund_policy.pdf#chunk_12
Reason:
  Chunk starts with connector word "except".

Why it matters:
  This chunk likely depends on a previous sentence and may lose the main rule.

Fix:
  Use sentence-aware splitting or increase overlap.

Snippet:
  except enterprise customers may request refunds within 90 days...
```

---

### JSON Report

```json
{
  "summary": {
    "chunks_scanned": 128,
    "issues_found": 19,
    "high": 4,
    "medium": 9,
    "low": 6
  },
  "issues": [
    {
      "chunk_id": "chunk_12",
      "source": "refund_policy.pdf",
      "rule_id": "starts_mid_sentence",
      "severity": "high",
      "reason": "Chunk starts with connector word 'except'.",
      "why_it_matters": "This chunk likely depends on a previous sentence and may lose the main rule.",
      "fix": "Use sentence-aware splitting or increase overlap.",
      "snippet": "except enterprise customers may request refunds within 90 days..."
    }
  ]
}
```

---

## 24. CI Behavior

### Exit Codes

```text
0 = passed
1 = failed lint threshold
2 = invalid input/config
3 = internal error
```

### Fail Threshold

```bash
chunklint scan chunks.json --fail-on high
```

Meaning:

```text
Fail if any high issue exists.
```

Also support:

```bash
chunklint scan chunks.json --fail-on medium
chunklint scan chunks.json --fail-on low
```

---

## 25. GitHub Actions Integration

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
        run: |
          pip install chunklint
          pip install -r requirements.txt

      - name: Generate chunks
        run: python scripts/generate_chunks.py

      - name: Run ChunkLint
        run: chunklint scan chunks.json --fail-on high
```

---

## 26. Acceptance Criteria

ChunkLint v1 is complete when:

- CLI can scan JSON and JSONL chunks
- SDK can lint `list[dict]`
- LangChain adapter can lint `list[Document]`
- LlamaIndex adapter can lint `list[Node]`
- At least 10 rules work
- Terminal report is readable
- JSON export works
- `--fail-on high` works
- Config file works
- Unit tests exist for each rule
- README has LangChain and LlamaIndex examples

---

## 27. Example End-to-End Demo

### Bad Input

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
  },
  {
    "id": "chunk_2",
    "text": "except enterprise customers may request refunds within 90 days.",
    "source": "refund_policy.pdf",
    "metadata": {
      "page": 2,
      "heading": "Refund Policy"
    }
  },
  {
    "id": "chunk_3",
    "text": "| Pro | $29 |
| Enterprise | Contact sales |",
    "source": "pricing.md",
    "metadata": {}
  }
]
```

### Command

```bash
chunklint scan bad_chunks.json --fail-on high
```

### Output

```text
ChunkLint Report

Chunks scanned: 3
Issues found: 4

High: 2
Medium: 2
Low: 0

HIGH starts_mid_sentence chunk_2
Reason: Chunk starts with connector word "except".
Fix: Use sentence-aware splitting or increase overlap.

HIGH broken_markdown_table chunk_3
Reason: Table rows found but table header is missing.
Fix: Repeat table headers in every table chunk.

MEDIUM missing_heading chunk_3
Reason: Chunk has no heading/title metadata.
Fix: Add heading, section, or document title metadata.

MEDIUM too_short chunk_3
Reason: Chunk has only 7 words.
Fix: Merge with nearby context or include table header.
```

Exit code: `1`.

---

## 28. Roadmap

### Week 1: Core Package

Build:

- Python package setup
- Data models
- JSON/JSONL loader
- CLI `scan` command
- Terminal report
- Rules:
  - `missing_text`
  - `missing_id`
  - `missing_source`
  - `too_short`
  - `too_long`

---

### Week 2: RAG-Specific Rules

Build:

- `missing_heading`
- `starts_mid_sentence`
- `ends_mid_sentence`
- `broken_markdown_table`
- `broken_code_block`

---

### Week 3: Integrations

Build:

- LangChain adapter
- LlamaIndex adapter
- Export helpers
- Examples
- Unit tests

---

### Week 4: CI and Polish

Build:

- `near_duplicate`
- `pdf_noise`
- Config file support
- `--fail-on` behavior
- JSON output
- GitHub Actions example
- README
- PyPI release

---

## 29. Future v2 Ideas

Only after v1 is strong:

- HTML report
- SARIF output for GitHub code scanning
- Direct Chroma scan
- Direct Qdrant scan
- Direct Pinecone scan
- Direct Weaviate scan
- Markdown file scanning directly
- PDF text extraction mode
- Auto-fix suggestions
- Plugin system
- Rule packs:
  - `chunklint-rules-policy-docs`
  - `chunklint-rules-code-docs`
  - `chunklint-rules-support-docs`

Best v2 feature:

> SARIF output, so ChunkLint issues can appear directly inside GitHub PRs.

---

## 30. README Positioning

Use this framing:

```text
# ChunkLint

ChunkLint is a static analyzer for RAG chunks.

It catches broken boundaries, missing headings, malformed markdown tables,
broken code blocks, duplicate chunks, and missing metadata before your chunks
enter a vector database.

No LLM calls. No embeddings. No eval dataset. Fast enough for CI.
```

Example:

```bash
chunklint scan chunks.json --fail-on high
```

SDK:

```python
from chunklint.adapters.langchain import lint_documents

chunks = splitter.split_documents(docs)
report = lint_documents(chunks)

if report.has_high_issues:
    report.print()
else:
    vectorstore.add_documents(chunks)
```

---

## 31. Final Product Definition

### Product

**ChunkLint**

### Category

Developer tool / RAG quality / static analyzer

### Problem

Bad RAG chunks silently enter vector databases and cause retrieval failures later.

### Solution

A Python SDK and CLI that statically analyzes chunks and flags obvious structural issues before indexing.

### Core Wedge

> CI checks for RAG chunk quality.

### MVP

- JSON/JSONL input
- Python SDK
- LangChain adapter
- LlamaIndex adapter
- 10+ static lint rules
- Terminal report
- JSON export
- Config file
- CI fail mode

### Final Pitch

> **ChunkLint is ESLint for RAG chunks — a no-LLM static analyzer that catches broken, context-missing, duplicate, or malformed chunks before they enter your vector database.**
