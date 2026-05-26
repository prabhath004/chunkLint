import json

import pytest

from chunklint.loader import export_chunks, load_chunks


def test_load_json_array(tmp_path):
    path = tmp_path / "chunks.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "chunk_1",
                    "text": "Refund Policy. Customers can request refunds within 30 days.",
                    "source": "refund_policy.md",
                    "metadata": {"heading": "Refund Policy"},
                }
            ]
        )
    )

    chunks = load_chunks(path)

    assert len(chunks) == 1
    assert chunks[0].id == "chunk_1"
    assert chunks[0].source == "refund_policy.md"


def test_load_jsonl(tmp_path):
    path = tmp_path / "chunks.jsonl"
    path.write_text(
        '{"id":"chunk_1","text":"Refund Policy. Customers can request refunds.",'
        '"metadata":{"source":"refund_policy.md","heading":"Refund Policy"}}\n'
    )

    chunks = load_chunks(path)

    assert chunks[0].source == "refund_policy.md"


def test_export_chunks_jsonl(tmp_path):
    path = tmp_path / "chunks.jsonl"

    export_chunks([{"id": "chunk_1", "text": "Hello.", "source": "a.md"}], path)

    assert json.loads(path.read_text().strip())["id"] == "chunk_1"


def test_load_json_with_chunks_envelope(tmp_path):
    path = tmp_path / "chunks.json"
    path.write_text(
        json.dumps(
            {
                "chunks": [
                    {"id": "chunk_1", "text": "Hello.", "source": "a.md"},
                ]
            }
        )
    )

    chunks = load_chunks(path)

    assert len(chunks) == 1
    assert chunks[0].id == "chunk_1"


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(ValueError, match="does not exist"):
        load_chunks(tmp_path / "missing.json")


def test_load_malformed_json_raises(tmp_path):
    path = tmp_path / "chunks.json"
    path.write_text("{not valid json")
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_chunks(path)


def test_load_empty_json_file_raises(tmp_path):
    path = tmp_path / "chunks.json"
    path.write_text("")
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_chunks(path)


def test_load_json_object_without_chunks_key_raises(tmp_path):
    path = tmp_path / "chunks.json"
    path.write_text(json.dumps({"unrelated": [1, 2, 3]}))
    with pytest.raises(ValueError, match="array of chunks"):
        load_chunks(path)


def test_load_json_non_array_top_level_raises(tmp_path):
    path = tmp_path / "chunks.json"
    path.write_text(json.dumps("just a string"))
    with pytest.raises(ValueError, match="array of chunks"):
        load_chunks(path)


def test_load_jsonl_with_invalid_line_raises(tmp_path):
    path = tmp_path / "chunks.jsonl"
    path.write_text(
        '{"id": "chunk_1", "text": "ok", "source": "a.md"}\n'
        "not valid json on line 2\n"
    )
    with pytest.raises(ValueError, match="line 2"):
        load_chunks(path)


def test_load_jsonl_with_non_object_line_raises(tmp_path):
    path = tmp_path / "chunks.jsonl"
    path.write_text(
        '{"id": "chunk_1", "text": "ok", "source": "a.md"}\n'
        '"this is a string, not an object"\n'
    )
    with pytest.raises(ValueError, match="must be an object"):
        load_chunks(path)


def test_load_jsonl_ignores_blank_lines(tmp_path):
    path = tmp_path / "chunks.jsonl"
    path.write_text(
        '\n'
        '{"id": "chunk_1", "text": "ok", "source": "a.md"}\n'
        '   \n'
        '{"id": "chunk_2", "text": "ok2", "source": "b.md"}\n'
    )
    chunks = load_chunks(path)
    assert [chunk.id for chunk in chunks] == ["chunk_1", "chunk_2"]

