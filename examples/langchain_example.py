from chunklint.adapters.langchain import export_documents, lint_documents


docs = loader.load()
chunks = splitter.split_documents(docs)

report = lint_documents(chunks)
export_documents(chunks, "chunks.json")

if report.has_high_issues:
    raise RuntimeError(
        "ChunkLint found high-severity findings. "
        "Run: chunklint scan chunks.json --verbose"
    )

vectorstore.add_documents(chunks)
