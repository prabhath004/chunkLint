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

    result = runner.invoke(app, ["init", "--path", str(path)])

    assert result.exit_code == 0
    assert "missing_text" in path.read_text()
