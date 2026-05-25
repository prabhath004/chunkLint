from chunklint.adapters.langchain import lint_documents


docs = loader.load()
chunks = splitter.split_documents(docs)

report = lint_documents(chunks)

if report.has_high_issues:
    report.print()
    raise RuntimeError("ChunkLint failed")

vectorstore.add_documents(chunks)

