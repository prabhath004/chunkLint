from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table

from chunklint.models import Issue, LintReport


@dataclass(frozen=True)
class IssueGroup:
    rule_id: str
    count: int
    highest_severity: str
    affected_chunks: int
    example_reason: str
    example_fix: str


SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3}


def print_report(
    report: LintReport,
    *,
    console: Console | None = None,
    max_issues: int = 20,
    verbose: bool = False,
) -> None:
    console = console or Console()
    console.print("[bold]ChunkLint Report[/bold]")
    console.print()
    console.print(f"Chunks scanned: {report.chunks_scanned}")
    console.print(f"Issues found: {report.issues_found}")
    console.print()
    console.print(f"High:   {report.high}")
    console.print(f"Medium: {report.medium}")
    console.print(f"Low:    {report.low}")

    if not report.issues:
        console.print()
        console.print("[green]No issues found.[/green]")
        return

    console.print()
    console.print("[bold]Issue groups:[/bold]")
    group_table = Table(show_header=True, header_style="bold")
    group_table.add_column("Rule")
    group_table.add_column("Issues", justify="right")
    group_table.add_column("Chunks", justify="right")
    group_table.add_column("Max")
    group_table.add_column("Example")
    for group in group_issues(report.issues):
        group_table.add_row(
            group.rule_id,
            str(group.count),
            str(group.affected_chunks),
            group.highest_severity.upper(),
            group.example_reason,
        )
    console.print(group_table)

    recommendations = build_recommendations(report.issues)
    if recommendations:
        console.print()
        console.print("[bold]Recommended next steps:[/bold]")
        for recommendation in recommendations:
            console.print(f"- {recommendation}")

    console.print()
    detail_issues = report.issues if verbose else report.issues[:max_issues]
    hidden = len(report.issues) - len(detail_issues)
    if hidden > 0:
        console.print(
            f"[bold]Detailed issues:[/bold] showing first {len(detail_issues)} "
            f"of {len(report.issues)}. Use --verbose to show all."
        )
    else:
        console.print("[bold]Detailed issues:[/bold]")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Sev")
    table.add_column("Rule")
    table.add_column("Chunk")
    table.add_column("Reason")
    table.add_column("Fix")
    for issue in detail_issues:
        chunk_label = issue.chunk_id or issue.source or "-"
        table.add_row(
            issue.severity.upper(),
            issue.rule_id,
            chunk_label,
            issue.reason,
            issue.fix,
        )
    console.print(table)


def report_json(report: LintReport) -> str:
    payload = report.as_json_dict()
    payload["groups"] = [group.__dict__ for group in group_issues(report.issues)]
    payload["recommendations"] = build_recommendations(report.issues)
    return json.dumps(payload, indent=2, ensure_ascii=False)


def group_issues(issues: list[Issue]) -> list[IssueGroup]:
    grouped: dict[str, list[Issue]] = {}
    for issue in issues:
        grouped.setdefault(issue.rule_id, []).append(issue)

    groups: list[IssueGroup] = []
    for rule_id, rule_issues in grouped.items():
        highest = max(rule_issues, key=lambda issue: SEVERITY_RANK.get(issue.severity, 0))
        affected_chunks = {
            issue.chunk_id or issue.source or f"issue-{index}"
            for index, issue in enumerate(rule_issues)
        }
        groups.append(
            IssueGroup(
                rule_id=rule_id,
                count=len(rule_issues),
                highest_severity=highest.severity,
                affected_chunks=len(affected_chunks),
                example_reason=rule_issues[0].reason,
                example_fix=rule_issues[0].fix,
            )
        )

    return sorted(
        groups,
        key=lambda group: (
            SEVERITY_RANK.get(group.highest_severity, 0),
            group.count,
            group.rule_id,
        ),
        reverse=True,
    )


def build_recommendations(issues: list[Issue]) -> list[str]:
    counts = Counter(issue.rule_id for issue in issues)
    recommendations: list[str] = []

    boundary_count = (
        counts["starts_mid_sentence"]
        + counts["ends_mid_sentence"]
        + counts["broken_chunk_boundary"]
    )
    if boundary_count:
        recommendations.append(
            "Boundary issues dominate. Try sentence-aware splitting, larger chunks, "
            "or more overlap before embedding."
        )
    if counts["pdf_noise"]:
        recommendations.append(
            "PDF noise was detected. Strip page numbers/repeated headers and normalize "
            "PDF whitespace before chunking."
        )
    if counts["missing_heading"]:
        recommendations.append(
            "Add section/title metadata during loading or post-processing so chunks keep "
            "retrievable context."
        )
    if counts["broken_markdown_table"]:
        recommendations.append(
            "Repeat markdown table headers in every table chunk or split tables as whole blocks."
        )
    if counts["broken_code_block"]:
        recommendations.append("Keep fenced code blocks intact when splitting documentation.")
    if counts["near_duplicate"]:
        recommendations.append("Reduce splitter overlap or deduplicate chunks before embedding.")
    if counts["too_short"] > counts["too_long"]:
        recommendations.append("Merge tiny chunks with neighboring context or lower split aggressiveness.")
    elif counts["too_long"]:
        recommendations.append("Split very large chunks by section or paragraph before embedding.")

    return recommendations[:5]
