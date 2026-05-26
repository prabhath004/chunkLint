from chunklint.adapters.llamaindex import export_nodes, lint_nodes


nodes = parser.get_nodes_from_documents(documents)

report = lint_nodes(nodes)
export_nodes(nodes, "chunks.json")

if report.has_high_issues:
    raise RuntimeError(
        "ChunkLint found high-severity findings. "
        "Run: chunklint scan chunks.json --verbose"
    )

index = VectorStoreIndex(nodes)
