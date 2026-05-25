from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from chunklint.models import Chunk
from chunklint.normalizer import chunks_to_jsonable, normalize_chunks


def load_chunks(path: str | Path) -> list[Chunk]:
    input_path = Path(path)
    if not input_path.exists():
        raise ValueError(f"Input file does not exist: {input_path}")
    if input_path.suffix.lower() == ".jsonl":
        return _load_jsonl(input_path)
    return _load_json(input_path)


def export_chunks(chunks: Iterable[Any], path: str | Path) -> None:
    output_path = Path(path)
    rows = chunks_to_jsonable(chunks)
    if output_path.suffix.lower() == ".jsonl":
        output_path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n"
        )
        return
    output_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")


def _load_json(path: Path) -> list[Chunk]:
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if isinstance(payload, dict) and "chunks" in payload:
        payload = payload["chunks"]
    if not isinstance(payload, list):
        raise ValueError("JSON input must be an array of chunks or an object with a chunks array.")
    return normalize_chunks(payload)


def _load_jsonl(path: Path) -> list[Chunk]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            row = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL on line {line_number}: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"JSONL line {line_number} must be an object.")
        rows.append(row)
    return normalize_chunks(rows)

