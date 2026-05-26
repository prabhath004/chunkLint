import json

from typer.testing import CliRunner

from chunklint.cli import app

runner = CliRunner()


def test_cli_scan_json_fails_on_high(tmp_path):
    path = tmp_path / "chunks.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "chunk_2",
                    "text": "except enterprise customers may request refunds within 90 days.",
                    "source": "refund_policy.pdf",
                    "metadata": {"heading": "Refund Policy"},
                }
            ]
        )
    )

    result = runner.invoke(app, ["scan", str(path), "--fail-on", "high", "--quiet"])

    assert result.exit_code == 1


def test_cli_fail_on_prints_gate_status(tmp_path):
    path = write_gate_fixture(tmp_path)

    result = runner.invoke(app, ["scan", str(path), "--fail-on", "high"])

    assert result.exit_code == 1
    assert "ChunkLint Gate" in result.output
    assert "ChunkLint Report" not in result.output
    assert "Gate result" in result.output
    assert "FAILED" in result.output
    assert "Selected severity" in result.output
    assert "high" in result.output
    assert "All findings" in result.output
    assert "6 (2 high, 2 medium, 2 low)" in result.output
    assert "Selected findings" in result.output
    assert "2 (2 high)" in result.output
    assert "Other findings" in result.output
    assert "Overall Lint Report" in result.output
    assert "Shown findings:" not in result.output
    assert "Raw findings:" not in result.output
    assert "High Root Causes" in result.output
    assert "Markdown tables" in result.output
    assert "Sentence boundaries" in result.output
    blocking_section = result.output.split("High Root Causes", 1)[1]
    blocking_section = blocking_section.split("Next Steps", 1)[0]
    assert "Chunk size" not in blocking_section
    assert "Missing retrieval context" not in blocking_section


def test_cli_fail_on_medium_hides_low_only(tmp_path):
    path = write_gate_fixture(tmp_path)

    result = runner.invoke(app, ["scan", str(path), "--fail-on", "medium"])

    assert result.exit_code == 1
    assert "Selected severity" in result.output
    assert "medium" in result.output
    assert "Selected findings" in result.output
    assert "2 (2 medium)" in result.output
    assert "Overall Lint Report" in result.output
    assert "Medium Root Causes" in result.output
    assert "Chunk size" in result.output
    assert "Missing retrieval" in result.output
    assert "context" in result.output
    selected_section = result.output.split("Medium Root Causes", 1)[1]
    selected_section = selected_section.split("Next Steps", 1)[0]
    assert "Markdown tables" not in selected_section


def test_cli_fail_on_low_shows_only_low_root_causes(tmp_path):
    path = write_gate_fixture(tmp_path)

    result = runner.invoke(app, ["scan", str(path), "--fail-on", "low"])

    assert result.exit_code == 1
    assert "Selected severity" in result.output
    assert "low" in result.output
    assert "Selected findings" in result.output
    assert "2 (2 low)" in result.output
    assert "Overall Lint Report" in result.output
    assert "Low Root Causes" in result.output
    selected_section = result.output.split("Low Root Causes", 1)[1]
    selected_section = selected_section.split("Next Steps", 1)[0]
    assert "Chunk size" in selected_section
    assert "Markdown tables" not in selected_section
    assert "Missing retrieval" not in selected_section


def test_cli_fail_on_passes_with_only_lower_severity_findings(tmp_path):
    path = tmp_path / "chunks.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "tiny",
                    "text": "Short.",
                    "source": "notes.md",
                    "metadata": {"heading": "Notes"},
                }
            ]
        )
    )

    result = runner.invoke(app, ["scan", str(path), "--fail-on", "high"])

    assert result.exit_code == 0
    assert "ChunkLint Gate" in result.output
    assert "Gate result" in result.output
    assert "PASSED" in result.output
    assert "Selected findings" in result.output
    assert "Overall Lint Report" in result.output
    assert "No high findings." in result.output


def test_cli_json_with_fail_on_stays_json_only(tmp_path):
    path = write_gate_fixture(tmp_path)

    result = runner.invoke(app, ["scan", str(path), "--fail-on", "high", "--format", "json"])

    payload = json.loads(result.output)

    assert result.exit_code == 1
    assert payload["summary"]["high"] == 2
    assert "ChunkLint Gate" not in result.output


def test_cli_fail_on_rejects_unknown_severity(tmp_path):
    path = write_gate_fixture(tmp_path)

    result = runner.invoke(app, ["scan", str(path), "--fail-on", "hish"])

    assert result.exit_code == 2
    normalized = " ".join(result.output.split())
    assert 'Unsupported severity "hish". Choose one of: high, medium, low.' in normalized


def test_cli_fail_on_accepts_comma_list(tmp_path):
    path = write_gate_fixture(tmp_path)

    result = runner.invoke(app, ["scan", str(path), "--fail-on", "high,medium"])

    assert result.exit_code == 1
    assert "Selected severities" in result.output
    assert "high, medium" in result.output
    assert "Selected findings" in result.output
    assert "4 (2 high, 2 medium)" in result.output
    assert "Blocking Root Causes (high, medium)" in result.output


def test_cli_fail_on_comma_list_ignores_low_only_corpus(tmp_path):
    path = tmp_path / "chunks.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "tiny",
                    "text": "Short.",
                    "source": "notes.md",
                    "metadata": {"heading": "Notes"},
                }
            ]
        )
    )

    result = runner.invoke(app, ["scan", str(path), "--fail-on", "high,medium"])

    assert result.exit_code == 0
    assert "PASSED" in result.output
    assert "No high, medium findings." in result.output


def test_cli_fail_on_empty_value_is_rejected(tmp_path):
    path = write_gate_fixture(tmp_path)

    result = runner.invoke(app, ["scan", str(path), "--fail-on", ""])

    assert result.exit_code == 2
    assert "at least one severity" in result.output


def test_cli_fail_on_at_or_above_expands_to_threshold_set(tmp_path):
    path = write_gate_fixture(tmp_path)

    result = runner.invoke(app, ["scan", str(path), "--fail-on-at-or-above", "medium"])

    assert result.exit_code == 1
    assert "Selected severities" in result.output
    assert "high, medium" in result.output
    assert "Blocking Root Causes (high, medium)" in result.output


def test_cli_fail_on_at_or_above_low_includes_all_severities(tmp_path):
    path = write_gate_fixture(tmp_path)

    result = runner.invoke(app, ["scan", str(path), "--fail-on-at-or-above", "low"])

    assert result.exit_code == 1
    assert "high, medium, low" in result.output


def test_cli_fail_on_at_or_above_passes_when_below_threshold(tmp_path):
    path = tmp_path / "chunks.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "tiny",
                    "text": "Short.",
                    "source": "notes.md",
                    "metadata": {"heading": "Notes"},
                }
            ]
        )
    )

    result = runner.invoke(app, ["scan", str(path), "--fail-on-at-or-above", "high"])

    assert result.exit_code == 0
    assert "PASSED" in result.output


def test_cli_fail_on_and_fail_on_at_or_above_are_mutually_exclusive(tmp_path):
    path = write_gate_fixture(tmp_path)

    result = runner.invoke(
        app,
        ["scan", str(path), "--fail-on", "high", "--fail-on-at-or-above", "medium"],
    )

    assert result.exit_code == 2
    assert "mutually exclusive" in result.output


def test_cli_fail_on_at_or_above_rejects_unknown_severity(tmp_path):
    path = write_gate_fixture(tmp_path)

    result = runner.invoke(app, ["scan", str(path), "--fail-on-at-or-above", "huge"])

    assert result.exit_code == 2
    normalized = " ".join(result.output.split())
    assert 'Unsupported severity "huge"' in normalized


def test_cli_scan_writes_json_report(tmp_path):
    path = tmp_path / "chunks.json"
    out = tmp_path / "report.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "chunk_1",
                    "text": "Refund Policy. Customers can request refunds within 30 days.",
                    "source": "refund_policy.pdf",
                    "metadata": {"heading": "Refund Policy"},
                }
            ]
        )
    )

    result = runner.invoke(app, ["scan", str(path), "--out", str(out), "--quiet"])

    assert result.exit_code == 0
    assert json.loads(out.read_text())["summary"]["chunks_scanned"] == 1


def test_cli_init_creates_config(tmp_path):
    path = tmp_path / "chunklint.yml"

    result = runner.invoke(app, ["init", str(path)])

    assert result.exit_code == 0
    assert "missing_text" in path.read_text()


def write_gate_fixture(tmp_path):
    path = tmp_path / "chunks.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "chunk_1",
                    "text": "Refund Policy. Customers can request refunds within 30 days.",
                    "source": "refund_policy.pdf",
                    "metadata": {"page": 2, "heading": "Refund Policy"},
                },
                {
                    "id": "chunk_2",
                    "text": "except enterprise customers may request refunds within 90 days.",
                    "source": "refund_policy.pdf",
                    "metadata": {"page": 2, "heading": "Refund Policy"},
                },
                {
                    "id": "chunk_3",
                    "text": "| Pro | $29 |\n| Enterprise | Contact sales |",
                    "source": "pricing.md",
                    "metadata": {},
                },
            ]
        )
    )
    return path
