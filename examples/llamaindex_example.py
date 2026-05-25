from chunklint.adapters.llamaindex import lint_nodes


nodes = parser.get_nodes_from_documents(documents)

report = lint_nodes(nodes)

if report.has_high_issues:
    report.print()
    raise RuntimeError("ChunkLint failed")

index = VectorStoreIndex(nodes)

