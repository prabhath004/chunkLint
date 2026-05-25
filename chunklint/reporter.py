from __future__ import annotations

import json
from collections import Counter

from rich.console import Console
from rich.table import Table

from chunklint.models import LintReport


def print_report(report: LintReport, *, console: Console | None = None) -> None:
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
    top_issues = Counter(issue.rule_id for issue in report.issues).most_common(5)
    console.print("[bold]Top issues:[/bold]")
    for rule_id, count in top_issues:
        console.print(f"- {rule_id}: {count}")

    console.print()
    table = Table(show_header=True, header_style="bold")
    table.add_column("Severity")
    table.add_column("Rule")
    table.add_column("Chunk")
    table.add_column("Reason")
    table.add_column("Fix")
    for issue in report.issues:
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
    return json.dumps(report.as_json_dict(), indent=2, ensure_ascii=False)

