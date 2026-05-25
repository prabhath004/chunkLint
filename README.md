# ChunkLint

ChunkLint is a static analyzer for RAG chunks.

It catches broken boundaries, missing headings, malformed markdown tables,
broken code blocks, duplicate chunks, and missing metadata before your chunks
enter a vector database.

No LLM calls. No embeddings. No eval dataset. Fast enough for CI.

## Install

```bash
pip install chunklint
```

For framework adapters:

```bash
pip install "chunklint[langchain]"
pip install "chunklint[llamaindex]"
```

## CLI

Scan JSON or JSONL chunk exports:

```bash
chunklint scan chunks.json --fail-on high
```

Write a JSON report:

```bash
chunklint scan chunks.json --format json --out report.json
```

Create a config file:

```bash
chunklint init
```

## Python SDK

```python
from chunklint import lint

chunks = [
    {
        "id": "chunk_1",
        "text": "Refund Policy. Customers can request refunds within 30 days.",
        "source": "refund_policy.md",
        "metadata": {"heading": "Refund Policy"},
    }
]

report = lint(chunks)

if report.has_high_issues:
    report.print()
    raise RuntimeError("ChunkLint failed")
```

## LangChain

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

## LlamaIndex

```python
from chunklint.adapters.llamaindex import lint_nodes

nodes = parser.get_nodes_from_documents(documents)
report = lint_nodes(nodes)

if report.has_high_issues:
    report.print()
else:
    index = VectorStoreIndex(nodes)
```

## Chunk Format

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

## Rules

- `missing_text`
- `missing_id`
- `missing_source`
- `missing_heading`
- `starts_mid_sentence`
- `ends_mid_sentence`
- `too_short`
- `too_long`
- `broken_markdown_table`
- `broken_code_block`
- `near_duplicate`
- `pdf_noise`
