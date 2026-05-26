"""Pin the public JSON output contract so consumers can rely on it.

The shape (key names + types) is part of the v1 public surface. Adding
a field is allowed; renaming or removing one requires bumping
JSON_SCHEMA_VERSION and is a breaking change.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from chunklint.cli import app
from chunklint.models import JSON_SCHEMA_VERSION

runner = CliRunner()


def _scan_fixture_json(tmp_path: Path) -> dict:
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
            ]
        )
    )
    result = runner.invoke(app, ["scan", str(path), "--format", "json"])
    assert result.exit_code == 0
    return json.loads(result.output)


def test_json_top_level_keys_are_frozen(tmp_path):
    payload = _scan_fixture_json(tmp_path)
    assert set(payload.keys()) == {
        "schema_version",
        "summary",
        "issues",
        "groups",
        "root_causes",
        "recommendations",
    }


def test_json_schema_version_is_pinned(tmp_path):
    payload = _scan_fixture_json(tmp_path)
    assert payload["schema_version"] == JSON_SCHEMA_VERSION
    assert payload["schema_version"] == 1


def test_json_summary_keys_are_frozen(tmp_path):
    payload = _scan_fixture_json(tmp_path)
    assert set(payload["summary"].keys()) == {
        "chunks_scanned",
        "issues_found",
        "high",
        "medium",
        "low",
    }
    for key in ("chunks_scanned", "issues_found", "high", "medium", "low"):
        assert isinstance(payload["summary"][key], int)


def test_json_issue_record_shape(tmp_path):
    payload = _scan_fixture_json(tmp_path)
    assert payload["issues"], "fixture is expected to surface at least one issue"
    issue = payload["issues"][0]
    assert set(issue.keys()) == {
        "chunk_id",
        "source",
        "rule_id",
        "severity",
        "reason",
        "why_it_matters",
        "fix",
        "snippet",
    }
    assert issue["severity"] in {"high", "medium", "low"}


def test_json_group_record_shape(tmp_path):
    payload = _scan_fixture_json(tmp_path)
    assert payload["groups"], "fixture is expected to surface at least one group"
    group = payload["groups"][0]
    assert set(group.keys()) == {
        "rule_id",
        "count",
        "highest_severity",
        "affected_chunks",
        "example_reason",
        "example_fix",
    }


def test_json_root_cause_record_shape(tmp_path):
    payload = _scan_fixture_json(tmp_path)
    assert payload["root_causes"], "fixture is expected to surface at least one root cause"
    root = payload["root_causes"][0]
    assert set(root.keys()) == {
        "id",
        "title",
        "rule_ids",
        "count",
        "highest_severity",
        "affected_chunks",
        "summary",
        "fix",
    }
    assert isinstance(root["rule_ids"], list)


def test_json_recommendations_are_strings(tmp_path):
    payload = _scan_fixture_json(tmp_path)
    assert isinstance(payload["recommendations"], list)
    for recommendation in payload["recommendations"]:
        assert isinstance(recommendation, str)
