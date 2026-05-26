from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from chunklint.engine import lint
from chunklint.loader import export_chunks
from chunklint.models import Chunk, LintReport
from chunklint.utils.metadata import source_from_metadata


def to_chunk(node: Any) -> Chunk:
    metadata = getattr(node, "metadata", {}) or {}
    return Chunk(
        id=getattr(node, "node_id", None),
        text=node.get_content(),
        source=source_from_metadata(metadata) or getattr(node, "ref_doc_id", None),
        metadata=metadata,
    )


def to_chunks(nodes: Iterable[Any]) -> list[Chunk]:
    return [to_chunk(node) for node in nodes]


def lint_nodes(nodes: Iterable[Any], **kwargs: Any) -> LintReport:
    return lint(to_chunks(nodes), **kwargs)


def export_nodes(nodes: Iterable[Any], path: str | Path) -> None:
    export_chunks(to_chunks(nodes), path)

