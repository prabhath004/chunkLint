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
    assert "Gate failed:" in result.output
    assert "--fail-on high matched 2 findings at or above high" in result.output
    assert "The report below is the full scan" in result.output
    assert result.output.index("Gate failed:") < result.output.index("ChunkLint Report")


def test_cli_fail_on_threshold_changes_gate_count(tmp_path):
    path = write_gate_fixture(tmp_path)

    result = runner.invoke(app, ["scan", str(path), "--fail-on", "low"])

    assert result.exit_code == 1
    assert "--fail-on low matched 6 findings at or above low" in result.output


def test_cli_json_with_fail_on_stays_json_only(tmp_path):
    path = write_gate_fixture(tmp_path)

    result = runner.invoke(app, ["scan", str(path), "--fail-on", "high", "--format", "json"])

    payload = json.loads(result.output)

    assert result.exit_code == 1
    assert payload["summary"]["high"] == 2
    assert "Gate failed" not in result.output


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
