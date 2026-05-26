from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from textwrap import shorten

from rich.console import Console
from rich.table import Table

from chunklint.models import Issue, LintReport
from chunklint.utils.severity import at_or_above, normalize_severity


@dataclass(frozen=True)
class IssueGroup:
    rule_id: str
    count: int
    highest_severity: str
    affected_chunks: int
    example_reason: str
    example_fix: str


@dataclass(frozen=True)
class RootCauseSpec:
    id: str
    title: str
    rule_ids: tuple[str, ...]
    summary: str
    fix: str


@dataclass(frozen=True)
class RootCauseGroup:
    id: str
    title: str
    rule_ids: tuple[str, ...]
    count: int
    highest_severity: str
    affected_chunks: int
    summary: str
    fix: str


SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3}
ROOT_CAUSE_SPECS = (
    RootCauseSpec(
        id="sentence_boundaries",
        title="Sentence boundaries",
        rule_ids=("broken_chunk_boundary", "starts_mid_sentence", "ends_mid_sentence"),
        summary="The splitter is cutting chunks through sentences.",
        fix="Use sentence-aware splitting, larger chunks, or more overlap before embedding.",
    ),
    RootCauseSpec(
        id="missing_retrieval_context",
        title="Missing retrieval context",
        rule_ids=("missing_heading",),
        summary="Chunks do not carry heading or section metadata.",
        fix="Add heading, section, title, document_title, or heading_path metadata during loading.",
    ),
    RootCauseSpec(
        id="pdf_extraction_noise",
        title="PDF extraction noise",
        rule_ids=("pdf_noise",),
        summary="PDF page, header, footer, or spacing artifacts remain in chunk text.",
        fix="Strip repeated PDF artifacts and normalize whitespace before splitting.",
    ),
    RootCauseSpec(
        id="chunk_size",
        title="Chunk size",
        rule_ids=("too_short", "too_long"),
        summary="The splitter is producing chunks outside the configured size range.",
        fix="Tune chunk size, overlap, and merge behavior.",
    ),
    RootCauseSpec(
        id="markdown_tables",
        title="Markdown tables",
        rule_ids=("broken_markdown_table",),
        summary="Table fragments are missing header or separator context.",
        fix="Keep tables intact or repeat table headers in every table chunk.",
    ),
    RootCauseSpec(
        id="code_blocks",
        title="Code blocks",
        rule_ids=("broken_code_block",),
        summary="Code fences are split across chunks.",
        fix="Keep fenced code blocks intact when splitting documentation.",
    ),
    RootCauseSpec(
        id="duplicate_chunks",
        title="Duplicate chunks",
        rule_ids=("near_duplicate",),
        summary="Chunks are highly similar to nearby chunks.",
        fix="Reduce overlap or deduplicate chunks before embedding.",
    ),
)
ROOT_CAUSE_BY_RULE = {
    rule_id: spec for spec in ROOT_CAUSE_SPECS for rule_id in spec.rule_ids
}
EXAMPLE_RULE_PRIORITY = {
    "broken_chunk_boundary": 50,
    "starts_mid_sentence": 40,
    "ends_mid_sentence": 30,
}


def print_report(
    report: LintReport,
    *,
    console: Console | None = None,
    max_issues: int = 20,
    verbose: bool = False,
    examples_per_rule: int = 3,
    raw: bool = False,
    focus_threshold: str | None = None,
) -> None:
    console = console or Console()
    console.print("[bold]ChunkLint Report[/bold]")
    console.print()
    console.print(f"Chunks scanned: {report.chunks_scanned}")
    root_causes = group_root_causes(report.issues)
    if focus_threshold is None:
        console.print(f"Raw findings: {report.issues_found}")
    else:
        console.print(
            f"Shown findings: {report.issues_found} at or above {focus_threshold}"
        )
    if root_causes:
        console.print(f"Actionable root causes: {len(root_causes)}")
    console.print()
    console.print(f"High:   {report.high}")
    console.print(f"Medium: {report.medium}")
    console.print(f"Low:    {report.low}")

    if not report.issues:
        console.print()
        if focus_threshold is None:
            console.print("[green]No issues found.[/green]")
        else:
            console.print(f"[green]No findings at or above {focus_threshold}.[/green]")
        return

    console.print()
    console.print("[bold]Root causes:[/bold]")
    root_table = Table(show_header=True, header_style="bold")
    root_table.add_column("Root cause")
    root_table.add_column("Issues", justify="right")
    root_table.add_column("Chunks", justify="right")
    root_table.add_column("Max")
    root_table.add_column("What this means")
    for root_cause in root_causes:
        root_table.add_row(
            root_cause.title,
            str(root_cause.count),
            str(root_cause.affected_chunks),
            root_cause.highest_severity.upper(),
            root_cause.summary,
        )
    console.print(root_table)

    recommendations = build_recommendations(report.issues)
    if recommendations:
        console.print()
        console.print("[bold]Recommended next steps:[/bold]")
        for recommendation in recommendations:
            console.print(f"- {recommendation}")

    if verbose:
        console.print()
        console.print("[bold]Examples by root cause:[/bold]")
        _print_examples(
            report.issues,
            console=console,
            examples_per_rule=_examples_to_show(examples_per_rule),
            include_snippets=True,
        )

    if raw:
        console.print()
        _print_raw_issues(report, console=console, max_issues=max_issues)
    else:
        console.print()
        if verbose:
            console.print(
                "[dim]Use --raw for row-level debugging; use --raw --max-issues 0 "
                "to print every row.[/dim]"
            )
        else:
            console.print(
                "[dim]Use --verbose for examples with snippets. Use --raw for row-level "
                "debugging; use --raw --max-issues 0 to print every row.[/dim]"
            )


def print_gate_report(
    report: LintReport,
    threshold: str,
    *,
    console: Console | None = None,
    max_issues: int = 20,
    verbose: bool = False,
    examples_per_rule: int = 3,
    raw: bool = False,
) -> None:
    console = console or Console()
    threshold = normalize_severity(threshold)
    blocking_issues = [issue for issue in report.issues if at_or_above(issue.severity, threshold)]
    non_blocking_issues = [
        issue for issue in report.issues if not at_or_above(issue.severity, threshold)
    ]
    blocking_report = _report_from_issues(report.chunks_scanned, blocking_issues)
    blocking_root_causes = group_root_causes(blocking_issues)

    console.print("[bold]ChunkLint Gate[/bold]")
    console.print()
    if blocking_issues:
        console.print("[red]Status: FAILED[/red]")
    else:
        console.print("[green]Status: PASSED[/green]")
    console.print(f"Threshold: {threshold}")
    console.print(
        f"Blocking findings: {len(blocking_issues)}"
        f"{_format_breakdown_suffix(blocking_issues)}"
    )
    if non_blocking_issues:
        console.print(
            f"Lower-severity findings hidden: {len(non_blocking_issues)}"
            f"{_format_breakdown_suffix(non_blocking_issues)}"
        )
        console.print(
            "Hidden lower-severity details: "
            f"{_format_hidden_root_cause_summary(non_blocking_issues, blocking_root_causes)}"
        )
    console.print(f"Chunks scanned: {report.chunks_scanned}")

    if not blocking_issues:
        console.print()
        console.print(f"[green]No findings at or above {threshold}.[/green]")
        if non_blocking_issues:
            console.print(
                "[dim]Run without --fail-on for the full diagnostic report.[/dim]"
            )
        return

    console.print()
    console.print("[bold]Blocking root causes:[/bold]")
    root_table = Table(show_header=True, header_style="bold")
    root_table.add_column("Root cause")
    root_table.add_column("Findings", justify="right")
    root_table.add_column("Chunks", justify="right")
    root_table.add_column("Max")
    root_table.add_column("Fix")
    for root_cause in blocking_root_causes:
        root_table.add_row(
            root_cause.title,
            str(root_cause.count),
            str(root_cause.affected_chunks),
            root_cause.highest_severity.upper(),
            root_cause.fix,
        )
    console.print(root_table)

    recommendations = build_recommendations(blocking_issues)
    if recommendations:
        console.print()
        console.print("[bold]Blocking next steps:[/bold]")
        for recommendation in recommendations:
            console.print(f"- {recommendation}")

    if verbose:
        console.print()
        console.print("[bold]Blocking examples:[/bold]")
        _print_examples(
            blocking_issues,
            console=console,
            examples_per_rule=_examples_to_show(examples_per_rule),
            include_snippets=True,
        )

    if raw:
        console.print()
        _print_raw_issues(blocking_report, console=console, max_issues=max_issues)
    else:
        console.print()
        if verbose:
            console.print(
                "[dim]Use --raw for blocking row-level findings; use --raw "
                "--max-issues 0 to print every blocking row.[/dim]"
            )
        else:
            console.print(
                "[dim]Use --verbose for blocking examples with snippets. Use --raw "
                "for blocking row-level findings. Run without --fail-on for the full "
                "diagnostic report.[/dim]"
            )


def _print_examples(
    issues: list[Issue],
    *,
    console: Console,
    examples_per_rule: int,
    include_snippets: bool,
) -> None:
    for root_cause, examples in examples_by_root_cause(issues, examples_per_rule):
        console.print(f"[bold]{root_cause.title}[/bold]")
        for issue in examples:
            chunk_label = issue.chunk_id or issue.source or "-"
            console.print(
                f"- {issue.rule_id} | {chunk_label}: {_compact(issue.reason, width=120)}"
            )
            if include_snippets and issue.snippet:
                console.print(f"  [dim]snippet: {_compact(issue.snippet, width=140)}[/dim]")


def _print_raw_issues(report: LintReport, *, console: Console, max_issues: int) -> None:
    if max_issues == 0:
        detail_issues = report.issues
    else:
        detail_issues = report.issues[:max(max_issues, 0)]
    hidden = len(report.issues) - len(detail_issues)
    if hidden > 0:
        console.print(
            f"[bold]Raw issue rows:[/bold] showing first {len(detail_issues)} "
            f"of {len(report.issues)}. Use --max-issues 0 to show all."
        )
    else:
        console.print("[bold]Raw issue rows:[/bold]")

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
    payload["groups"] = [asdict(group) for group in group_issues(report.issues)]
    payload["root_causes"] = [asdict(root_cause) for root_cause in group_root_causes(report.issues)]
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


def group_root_causes(issues: list[Issue]) -> list[RootCauseGroup]:
    grouped: dict[str, list[Issue]] = {}
    specs: dict[str, RootCauseSpec] = {}
    for issue in issues:
        spec = ROOT_CAUSE_BY_RULE.get(issue.rule_id, _fallback_root_cause(issue.rule_id))
        grouped.setdefault(spec.id, []).append(issue)
        specs[spec.id] = spec

    root_causes: list[RootCauseGroup] = []
    for root_id, root_issues in grouped.items():
        spec = specs[root_id]
        highest = max(root_issues, key=lambda issue: SEVERITY_RANK.get(issue.severity, 0))
        affected_chunks = {
            issue.chunk_id or issue.source or f"issue-{index}"
            for index, issue in enumerate(root_issues)
        }
        present_rules = tuple(
            rule_id for rule_id in spec.rule_ids if _has_rule(root_issues, rule_id)
        )
        root_causes.append(
            RootCauseGroup(
                id=spec.id,
                title=spec.title,
                rule_ids=present_rules or tuple(sorted({issue.rule_id for issue in root_issues})),
                count=len(root_issues),
                highest_severity=highest.severity,
                affected_chunks=len(affected_chunks),
                summary=spec.summary,
                fix=spec.fix,
            )
        )

    return sorted(
        root_causes,
        key=lambda root_cause: (
            SEVERITY_RANK.get(root_cause.highest_severity, 0),
            root_cause.count,
            root_cause.title,
        ),
        reverse=True,
    )


def examples_by_root_cause(
    issues: list[Issue],
    examples_per_rule: int = 3,
) -> list[tuple[RootCauseGroup, list[Issue]]]:
    examples_per_rule = max(examples_per_rule, 1)
    result: list[tuple[RootCauseGroup, list[Issue]]] = []
    for root_cause in group_root_causes(issues):
        root_issues = [issue for issue in issues if issue.rule_id in root_cause.rule_ids]
        result.append((root_cause, _select_examples(root_issues, examples_per_rule)))
    return result


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
        recommendations.append(
            "Merge tiny chunks with neighboring context or lower split aggressiveness."
        )
    elif counts["too_long"]:
        recommendations.append("Split very large chunks by section or paragraph before embedding.")

    return recommendations[:5]


def _report_from_issues(chunks_scanned: int, issues: list[Issue]) -> LintReport:
    counts = Counter(issue.severity for issue in issues)
    return LintReport(
        chunks_scanned=chunks_scanned,
        issues_found=len(issues),
        high=counts["high"],
        medium=counts["medium"],
        low=counts["low"],
        issues=issues,
    )


def _format_breakdown_suffix(issues: list[Issue]) -> str:
    breakdown = _severity_breakdown(issues)
    if not breakdown:
        return ""
    return f" ({breakdown})"


def _format_hidden_root_cause_summary(
    issues: list[Issue],
    blocking_root_causes: list[RootCauseGroup],
) -> str:
    blocking_root_cause_ids = {root_cause.id for root_cause in blocking_root_causes}
    return ", ".join(
        f"{root_cause.title} (+{root_cause.count} lower)"
        if root_cause.id in blocking_root_cause_ids
        else f"{root_cause.title} ({root_cause.count})"
        for root_cause in group_root_causes(issues)
    )


def _severity_breakdown(issues: list[Issue]) -> str:
    counts = Counter(issue.severity for issue in issues)
    parts = [
        f"{counts[severity]} {severity}"
        for severity in ("high", "medium", "low")
        if counts[severity]
    ]
    return ", ".join(parts)


def _select_examples(issues: list[Issue], limit: int) -> list[Issue]:
    ranked_issues = sorted(
        enumerate(issues),
        key=lambda indexed: (
            SEVERITY_RANK.get(indexed[1].severity, 0),
            EXAMPLE_RULE_PRIORITY.get(indexed[1].rule_id, 0),
            -indexed[0],
        ),
        reverse=True,
    )
    examples: list[Issue] = []
    seen_chunks: set[str] = set()
    for _, issue in ranked_issues:
        chunk_label = issue.chunk_id or issue.source or ""
        if chunk_label in seen_chunks:
            continue
        examples.append(issue)
        seen_chunks.add(chunk_label)
        if len(examples) >= limit:
            return examples

    for _, issue in ranked_issues:
        if issue in examples:
            continue
        examples.append(issue)
        if len(examples) >= limit:
            break
    return examples


def _fallback_root_cause(rule_id: str) -> RootCauseSpec:
    return RootCauseSpec(
        id=rule_id,
        title=rule_id.replace("_", " ").title(),
        rule_ids=(rule_id,),
        summary="This rule found repeated chunk quality issues.",
        fix="Inspect the examples and tune the loader, cleaner, or splitter.",
    )


def _examples_to_show(examples_per_rule: int) -> int:
    return max(examples_per_rule, 1)


def _has_rule(issues: list[Issue], rule_id: str) -> bool:
    return any(issue.rule_id == rule_id for issue in issues)


def _compact(text: str, width: int = 120) -> str:
    return shorten(" ".join(text.split()), width=width, placeholder="...")
