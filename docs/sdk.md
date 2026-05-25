# Python SDK

The SDK lets RAG pipelines lint chunks in memory before embedding them.

## Generic API

```python
from chunklint import lint

report = lint(chunks)
```

`chunks` can be:

- `list[dict]`
- `list[chunklint.Chunk]`
- LangChain `Document` objects
- LlamaIndex node objects
- Objects with a `text` attribute and optional `metadata`

## Dictionary Input

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
```

Dictionary normalization supports:

- `text`, `page_content`, or `content` for chunk text
- `id` or `chunk_id` for chunk ID
- top-level `source`
- metadata source keys such as `source`, `file_name`, `path`, and `document_id`

## Report Model

`lint()` returns `LintReport`.

```python
if report.ok:
    vectorstore.add_documents(chunks)

if report.has_high_issues:
    report.print()
```

Useful fields:

```python
report.chunks_scanned
report.issues_found
report.high
report.medium
report.low
report.issues
```

Each issue has:

```python
issue.chunk_id
issue.source
issue.rule_id
issue.severity
issue.reason
issue.why_it_matters
issue.fix
issue.snippet
```

## Config From Python

Pass a config path:

```python
from chunklint import lint

report = lint(chunks, config_path="chunklint.yml")
```

Or pass a config object:

```python
from chunklint import lint
from chunklint.config import default_config

config = default_config()
config.thresholds.min_words = 20

report = lint(chunks, config=config)
```

## LangChain Adapter

```python
from chunklint.adapters.langchain import export_documents, lint_documents

chunks = splitter.split_documents(docs)
report = lint_documents(chunks)

if report.has_high_issues:
    report.print()
    raise RuntimeError("ChunkLint failed")

export_documents(chunks, "chunks.json")
vectorstore.add_documents(chunks)
```

Mapping:

| LangChain field | ChunkLint field |
| --- | --- |
| `Document.page_content` | `Chunk.text` |
| `Document.id` | `Chunk.id` |
| `Document.metadata["source"]` | `Chunk.source` |
| `Document.metadata` | `Chunk.metadata` |

## LlamaIndex Adapter

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

Mapping:

| LlamaIndex field | ChunkLint field |
| --- | --- |
| `node.get_content()` | `Chunk.text` |
| `node.node_id` | `Chunk.id` |
| `node.metadata` | `Chunk.metadata` |
| `node.metadata["source"]` or `node.ref_doc_id` | `Chunk.source` |

## Export Helpers

Framework adapters can export chunks for CI or debugging:

```python
from chunklint.adapters.langchain import export_documents
from chunklint.adapters.llamaindex import export_nodes

export_documents(langchain_docs, "chunks.json")
export_nodes(llamaindex_nodes, "chunks.jsonl")
```

The extension controls the output format. `.jsonl` writes one chunk per line;
other paths write a formatted JSON array.

