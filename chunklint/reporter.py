from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from textwrap import shorten

from rich.console import Console
from rich.table import Table

from chunklint.models import Issue, LintReport
from chunklint.utils.severity import normalize_severity


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


@dataclass(frozen=True)
class ChunkOffender:
    chunk_label: str
    source: str | None
    count: int
    highest_severity: str
    rule_summary: str


SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3}
SEVERITY_BADGES = {
    "high": "[bold red]HIGH[/bold red]",
    "medium": "[yellow]MEDIUM[/yellow]",
    "low": "[cyan]LOW[/cyan]",
}


def _severity_badge(severity: str) -> str:
    return SEVERITY_BADGES.get(severity.lower(), severity.upper())

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
    elapsed: float | None = None,
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
        _print_elapsed(console, elapsed, report.chunks_scanned)
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
            _severity_badge(root_cause.highest_severity),
            root_cause.summary,
        )
    console.print(root_table)

    offenders = top_offending_chunks(report.issues)
    if offenders:
        console.print()
        console.print("[bold]Top offending chunks:[/bold]")
        _print_top_chunks_table(offenders, console=console)

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
    _print_elapsed(console, elapsed, report.chunks_scanned)


def print_gate_report(
    report: LintReport,
    threshold: str | list[str],
    *,
    console: Console | None = None,
    max_issues: int = 20,
    verbose: bool = False,
    examples_per_rule: int = 3,
    raw: bool = False,
    elapsed: float | None = None,
) -> None:
    console = console or Console()
    thresholds = _normalize_thresholds(threshold)
    threshold_set = set(thresholds)
    threshold_label = ", ".join(thresholds)
    blocking_issues = [
        issue for issue in report.issues if normalize_severity(issue.severity) in threshold_set
    ]
    non_blocking_issues = [
        issue for issue in report.issues if normalize_severity(issue.severity) not in threshold_set
    ]
    blocking_report = _report_from_issues(report.chunks_scanned, blocking_issues)
    blocking_root_causes = group_root_causes(blocking_issues)

    console.print("[bold]ChunkLint Gate[/bold]")
    console.print()
    _print_gate_summary_table(
        report,
        thresholds=thresholds,
        blocking_issues=blocking_issues,
        non_blocking_issues=non_blocking_issues,
        console=console,
    )

    console.print()
    console.print("[bold]Overall Lint Report[/bold]")
    _print_overall_lint_table(report, console=console)

    if not blocking_issues:
        console.print()
        console.print(f"[green]No {threshold_label} findings.[/green]")
        console.print("[dim]Run without --fail-on for the full diagnostic report.[/dim]")
        _print_elapsed(console, elapsed, report.chunks_scanned)
        return

    console.print()
    if len(thresholds) == 1:
        console.print(f"[bold]{thresholds[0].title()} Root Causes[/bold]")
    else:
        console.print(f"[bold]Blocking Root Causes ({threshold_label})[/bold]")
    _print_root_cause_table(blocking_root_causes, console=console)

    offenders = top_offending_chunks(blocking_issues)
    if offenders:
        console.print()
        console.print("[bold]Top offending chunks[/bold]")
        _print_top_chunks_table(offenders, console=console)

    recommendations = build_recommendations(blocking_issues)
    if recommendations:
        console.print()
        console.print("[bold]Next Steps[/bold]")
        _print_next_steps_table(recommendations, console=console)

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
                "[dim]Add --verbose for examples, --raw for selected rows, or run "
                "without --fail-on for the full diagnostic report.[/dim]"
            )
    _print_elapsed(console, elapsed, report.chunks_scanned)


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
            _severity_badge(issue.severity),
            issue.rule_id,
            chunk_label,
            issue.reason,
            issue.fix,
        )
    console.print(table)


def _print_gate_summary_table(
    report: LintReport,
    *,
    thresholds: list[str],
    blocking_issues: list[Issue],
    non_blocking_issues: list[Issue],
    console: Console,
) -> None:
    result = "[red]FAILED[/red]" if blocking_issues else "[green]PASSED[/green]"
    table = Table(show_header=True, header_style="bold")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Gate result", result)
    severity_label = "Selected severity" if len(thresholds) == 1 else "Selected severities"
    table.add_row(severity_label, ", ".join(thresholds))
    table.add_row("Chunks scanned", str(report.chunks_scanned))
    table.add_row(
        "All findings",
        f"{report.issues_found}{_format_report_breakdown_suffix(report)}",
    )
    table.add_row(
        "Selected findings",
        f"{len(blocking_issues)}{_format_breakdown_suffix(blocking_issues)}",
    )
    table.add_row(
        "Other findings",
        f"{len(non_blocking_issues)}{_format_breakdown_suffix(non_blocking_issues)}",
    )
    console.print(table)


def _print_overall_lint_table(report: LintReport, *, console: Console) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Severity")
    table.add_column("Findings", justify="right")
    table.add_row("High", str(report.high))
    table.add_row("Medium", str(report.medium))
    table.add_row("Low", str(report.low))
    table.add_row("Total", str(report.issues_found))
    console.print(table)


def _print_root_cause_table(
    root_causes: list[RootCauseGroup],
    *,
    console: Console,
) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", justify="right")
    table.add_column("Root cause")
    table.add_column("Severity")
    table.add_column("Findings", justify="right")
    table.add_column("Chunks", justify="right")
    table.add_column("Fix")
    for index, root_cause in enumerate(root_causes, start=1):
        table.add_row(
            str(index),
            root_cause.title,
            _severity_badge(root_cause.highest_severity),
            str(root_cause.count),
            str(root_cause.affected_chunks),
            root_cause.fix,
        )
    console.print(table)


def _print_top_chunks_table(offenders: list[ChunkOffender], *, console: Console) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Chunk")
    table.add_column("Issues", justify="right")
    table.add_column("Max")
    table.add_column("Top rules")
    for offender in offenders:
        table.add_row(
            offender.chunk_label,
            str(offender.count),
            _severity_badge(offender.highest_severity),
            offender.rule_summary,
        )
    console.print(table)


def _print_next_steps_table(recommendations: list[str], *, console: Console) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", justify="right")
    table.add_column("Action")
    for index, recommendation in enumerate(recommendations, start=1):
        table.add_row(str(index), recommendation)
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


def top_offending_chunks(issues: list[Issue], limit: int = 5) -> list[ChunkOffender]:
    if not issues:
        return []
    by_chunk: dict[str, list[Issue]] = {}
    sources: dict[str, str | None] = {}
    for issue in issues:
        label = issue.chunk_id or issue.source or "-"
        by_chunk.setdefault(label, []).append(issue)
        sources.setdefault(label, issue.source)
    offenders: list[ChunkOffender] = []
    for label, chunk_issues in by_chunk.items():
        highest = max(chunk_issues, key=lambda issue: SEVERITY_RANK.get(issue.severity, 0))
        rule_counts = Counter(issue.rule_id for issue in chunk_issues)
        ordered_rules = [rule for rule, _ in rule_counts.most_common()]
        top_rules = ordered_rules[:3]
        extra = len(ordered_rules) - len(top_rules)
        rule_summary = ", ".join(top_rules)
        if extra > 0:
            rule_summary += f", +{extra}"
        offenders.append(
            ChunkOffender(
                chunk_label=label,
                source=sources.get(label),
                count=len(chunk_issues),
                highest_severity=highest.severity,
                rule_summary=rule_summary,
            )
        )
    offenders.sort(
        key=lambda offender: (
            offender.count,
            SEVERITY_RANK.get(offender.highest_severity, 0),
            offender.chunk_label,
        ),
        reverse=True,
    )
    top = [offender for offender in offenders if offender.count >= 2][:max(limit, 0)]
    return top


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


def _severity_breakdown(issues: list[Issue]) -> str:
    counts = Counter(issue.severity for issue in issues)
    parts = [
        f"{counts[severity]} {severity}"
        for severity in ("high", "medium", "low")
        if counts[severity]
    ]
    return ", ".join(parts)


def _format_report_breakdown_suffix(report: LintReport) -> str:
    parts = [
        f"{count} {severity}"
        for severity, count in (
            ("high", report.high),
            ("medium", report.medium),
            ("low", report.low),
        )
        if count
    ]
    if not parts:
        return ""
    return f" ({', '.join(parts)})"


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


def _normalize_thresholds(threshold: str | list[str]) -> list[str]:
    if isinstance(threshold, str):
        raw = [threshold]
    else:
        raw = list(threshold)
    normalized: list[str] = []
    seen: set[str] = set()
    for value in raw:
        sev = normalize_severity(value)
        if sev not in seen:
            seen.add(sev)
            normalized.append(sev)
    if not normalized:
        raise ValueError("At least one severity is required.")
    return sorted(normalized, key=lambda sev: SEVERITY_RANK[sev], reverse=True)


def _format_elapsed(elapsed: float) -> str:
    if elapsed < 0.001:
        return "<1ms"
    if elapsed < 1:
        return f"{int(round(elapsed * 1000))}ms"
    return f"{elapsed:.2f}s"


def _print_elapsed(console: Console, elapsed: float | None, chunks_scanned: int) -> None:
    if elapsed is None:
        return
    console.print(
        f"[dim]Scanned {chunks_scanned} chunks in {_format_elapsed(elapsed)}.[/dim]"
    )
