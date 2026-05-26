import json

from chunklint.models import Issue, LintReport
from chunklint.reporter import build_recommendations, group_issues, report_json


def test_group_issues_summarizes_by_rule():
    issues = [
        issue("starts_mid_sentence", "high", "a"),
        issue("starts_mid_sentence", "high", "b"),
        issue("pdf_noise", "low", "a"),
    ]

    groups = group_issues(issues)

    assert groups[0].rule_id == "starts_mid_sentence"
    assert groups[0].count == 2
    assert groups[0].affected_chunks == 2


def test_report_json_includes_groups_and_recommendations():
    report = LintReport(
        chunks_scanned=2,
        issues_found=2,
        high=1,
        medium=1,
        low=0,
        issues=[
            issue("starts_mid_sentence", "high", "a"),
            issue("ends_mid_sentence", "medium", "a"),
        ],
    )

    payload = json.loads(report_json(report))

    assert payload["groups"][0]["rule_id"] in {"starts_mid_sentence", "ends_mid_sentence"}
    assert payload["recommendations"]


def test_build_recommendations_prioritizes_pdf_noise():
    recommendations = build_recommendations([issue("pdf_noise", "low", "a")])

    assert "PDF noise" in recommendations[0]


def issue(rule_id: str, severity: str, chunk_id: str) -> Issue:
    return Issue(
        chunk_id=chunk_id,
        source="source.pdf",
        rule_id=rule_id,
        severity=severity,
        reason=f"{rule_id} reason",
        why_it_matters="why",
        fix=f"{rule_id} fix",
        snippet="snippet",
    )
