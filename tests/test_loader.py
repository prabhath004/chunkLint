import json

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

