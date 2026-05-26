import json
from io import StringIO

from rich.console import Console

from chunklint.models import Issue, LintReport
from chunklint.reporter import (
    build_recommendations,
    examples_by_root_cause,
    group_issues,
    group_root_causes,
    print_report,
    report_json,
    top_offending_chunks,
)


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
    assert payload["root_causes"][0]["id"] == "sentence_boundaries"
    assert payload["recommendations"]


def test_group_root_causes_combines_boundary_rules():
    issues = [
        issue("starts_mid_sentence", "high", "b"),
        issue("ends_mid_sentence", "medium", "a"),
        issue("broken_chunk_boundary", "high", "b"),
        issue("missing_heading", "medium", "a"),
    ]

    root_causes = group_root_causes(issues)

    assert root_causes[0].id == "sentence_boundaries"
    assert root_causes[0].count == 3
    assert root_causes[0].affected_chunks == 2
    assert root_causes[0].rule_ids == (
        "broken_chunk_boundary",
        "starts_mid_sentence",
        "ends_mid_sentence",
    )


def test_examples_prioritize_broken_boundaries():
    issues = [
        issue("starts_mid_sentence", "high", "b"),
        issue("broken_chunk_boundary", "high", "c"),
        issue("ends_mid_sentence", "medium", "a"),
    ]

    examples = examples_by_root_cause(issues, examples_per_rule=1)

    assert examples[0][0].id == "sentence_boundaries"
    assert examples[0][1][0].rule_id == "broken_chunk_boundary"


def test_build_recommendations_prioritizes_pdf_noise():
    recommendations = build_recommendations([issue("pdf_noise", "low", "a")])

    assert "PDF noise" in recommendations[0]


def test_build_recommendations_quantifies_with_percentages():
    issues = [
        issue("starts_mid_sentence", "high", "chunk_a"),
        issue("starts_mid_sentence", "high", "chunk_b"),
        issue("pdf_noise", "low", "chunk_a"),
    ]

    recommendations = build_recommendations(issues, chunks_scanned=4)

    boundary = next(rec for rec in recommendations if "Boundary" in rec)
    pdf = next(rec for rec in recommendations if "PDF noise" in rec)
    assert "affects 2 of 4 chunks, 50%" in boundary
    assert "affects 1 of 4 chunks" in pdf


def test_build_recommendations_omits_percent_when_total_unknown():
    recommendations = build_recommendations([issue("pdf_noise", "low", "a")])

    assert "affects 1 chunks" in recommendations[0]


def test_print_report_is_summary_first_by_default():
    report = report_with_issues(
        [issue("starts_mid_sentence", "high", f"chunk-{index}") for index in range(5)]
    )

    output = render_report(report)

    assert "Root causes" in output
    assert "Raw findings: 5" in output
    assert "Actionable root causes: 1" in output
    assert "Examples by root cause" not in output
    assert "Use --verbose for examples" in output
    assert "chunk-4" not in output


def test_print_report_verbose_shows_examples_with_snippets():
    report = report_with_issues(
        [issue("starts_mid_sentence", "high", f"chunk-{index}") for index in range(2)]
    )

    output = render_report(report, verbose=True)

    assert "Examples by root cause" in output
    assert "chunk-0" in output
    assert "snippet:" in output
    assert "Use --verbose for examples" not in output
    assert "Use --raw for row-level debugging" in output


def test_print_report_raw_respects_max_issues():
    report = report_with_issues(
        [issue("starts_mid_sentence", "high", f"chunk-{index}") for index in range(5)]
    )

    output = render_report(report, raw=True, max_issues=2)

    assert "Raw issue rows:" in output
    assert "showing first 2 of 5" in output
    assert "chunk-0" in output
    assert "chunk-4" not in output


def test_print_report_raw_zero_shows_all_rows():
    report = report_with_issues(
        [issue("starts_mid_sentence", "high", f"chunk-{index}") for index in range(3)]
    )

    output = render_report(report, raw=True, max_issues=0)

    assert "showing first" not in output
    assert "chunk-2" in output


def test_top_offending_chunks_ranks_by_issue_count():
    issues = [
        issue("starts_mid_sentence", "high", "chunk_a"),
        issue("pdf_noise", "low", "chunk_a"),
        issue("missing_heading", "medium", "chunk_a"),
        issue("starts_mid_sentence", "high", "chunk_b"),
        issue("missing_heading", "medium", "chunk_b"),
        issue("starts_mid_sentence", "high", "chunk_c"),
    ]

    offenders = top_offending_chunks(issues)

    assert [offender.chunk_label for offender in offenders] == ["chunk_a", "chunk_b"]
    assert offenders[0].count == 3
    assert offenders[0].highest_severity == "high"


def test_top_offending_chunks_skips_single_issue_chunks():
    issues = [
        issue("starts_mid_sentence", "high", "chunk_a"),
        issue("pdf_noise", "low", "chunk_b"),
    ]

    assert top_offending_chunks(issues) == []


def test_top_offending_chunks_table_appears_in_default_report():
    issues = [
        issue("starts_mid_sentence", "high", "chunk_dense"),
        issue("pdf_noise", "low", "chunk_dense"),
        issue("missing_heading", "medium", "chunk_dense"),
    ]
    report = report_with_issues(issues)

    output = render_report(report)

    assert "Top offending chunks" in output
    assert "chunk_dense" in output


def report_with_issues(issues: list[Issue]) -> LintReport:
    return LintReport(
        chunks_scanned=len(issues),
        issues_found=len(issues),
        high=sum(1 for current in issues if current.severity == "high"),
        medium=sum(1 for current in issues if current.severity == "medium"),
        low=sum(1 for current in issues if current.severity == "low"),
        issues=issues,
    )


def render_report(report: LintReport, **kwargs: object) -> str:
    buffer = StringIO()
    console = Console(file=buffer, force_terminal=False, width=140)
    print_report(report, console=console, **kwargs)
    return buffer.getvalue()


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
