from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from chunklint.engine import lint
from chunklint.loader import export_chunks
from chunklint.models import Chunk, LintReport
from chunklint.utils.metadata import source_from_metadata


def to_chunk(document: Any) -> Chunk:
    metadata = getattr(document, "metadata", {}) or {}
    return Chunk(
        id=getattr(document, "id", None),
        text=getattr(document, "page_content", ""),
        source=source_from_metadata(metadata),
        metadata=metadata,
    )


def to_chunks(documents: Iterable[Any]) -> list[Chunk]:
    return [to_chunk(document) for document in documents]


def lint_documents(documents: Iterable[Any], **kwargs: Any) -> LintReport:
    return lint(to_chunks(documents), **kwargs)


def export_documents(documents: Iterable[Any], path: str | Path) -> None:
    export_chunks(to_chunks(documents), path)

