from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from chunklint.models import Chunk
from chunklint.utils.metadata import source_from_metadata


def normalize_chunks(items: Iterable[Any]) -> list[Chunk]:
    return [normalize_chunk(item) for item in items]


def normalize_chunk(item: Any) -> Chunk:
    if isinstance(item, Chunk):
        return item
    if isinstance(item, dict):
        return _from_mapping(item)
    if hasattr(item, "page_content"):
        return _from_langchain_document(item)
    if hasattr(item, "get_content"):
        return _from_llamaindex_node(item)
    if hasattr(item, "text"):
        metadata = getattr(item, "metadata", {}) or {}
        return Chunk(
            id=getattr(item, "id", None) or getattr(item, "node_id", None),
            text=item.text,
            source=getattr(item, "source", None) or source_from_metadata(metadata),
            metadata=metadata,
        )
    raise TypeError(f"Unsupported chunk type: {type(item).__name__}")


def chunks_to_jsonable(chunks: Iterable[Any]) -> list[dict[str, Any]]:
    return [chunk.model_dump(mode="json") for chunk in normalize_chunks(chunks)]


def _from_mapping(item: dict[str, Any]) -> Chunk:
    metadata = item.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {"value": metadata}
    text = item.get("text", item.get("page_content", item.get("content", "")))
    chunk_id = item.get("id", item.get("chunk_id"))
    source = item.get("source") or source_from_metadata(metadata)
    return Chunk(id=chunk_id, text=text, source=source, metadata=metadata)


def _from_langchain_document(document: Any) -> Chunk:
    metadata = getattr(document, "metadata", {}) or {}
    chunk_id = getattr(document, "id", None)
    return Chunk(
        id=chunk_id,
        text=getattr(document, "page_content", ""),
        source=source_from_metadata(metadata),
        metadata=metadata,
    )


def _from_llamaindex_node(node: Any) -> Chunk:
    metadata = getattr(node, "metadata", {}) or {}
    source = source_from_metadata(metadata) or getattr(node, "ref_doc_id", None)
    return Chunk(
        id=getattr(node, "node_id", None),
        text=node.get_content(),
        source=source,
        metadata=metadata,
    )

