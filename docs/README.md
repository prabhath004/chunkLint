# ChunkLint Documentation

This folder contains the working documentation for ChunkLint users and
contributors.

## Pages

- [CLI](cli.md): commands, options, exit codes, and examples.
- [SDK](sdk.md): Python API, report model, LangChain adapter, and LlamaIndex adapter.
- [Rules](rules.md): rule behavior, severities, thresholds, and config.
- [Testing](testing.md): what each test file covers and how to run the suite.

## Product Boundary

ChunkLint is a pre-index static analyzer for RAG chunks. It does not parse PDFs,
call LLMs, compute embeddings, connect to vector databases, or judge answer
quality. It checks chunk structure before the expensive part of the pipeline.

