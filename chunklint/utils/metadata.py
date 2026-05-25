from __future__ import annotations

from typing import Any


SOURCE_KEYS = ("source", "file", "file_name", "filename", "path", "file_path", "document_id")


def first_present(mapping: dict[str, Any], keys: list[str] | tuple[str, ...]) -> Any | None:
    for key in keys:
        value = mapping.get(key)
        if value is not None and str(value).strip():
            return value
    return None


def source_from_metadata(metadata: dict[str, Any]) -> str | None:
    value = first_present(metadata, SOURCE_KEYS)
    if value is None:
        return None
    return str(value)


def has_heading_metadata(metadata: dict[str, Any], heading_keys: list[str]) -> bool:
    return first_present(metadata, heading_keys) is not None

