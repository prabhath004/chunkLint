from __future__ import annotations

import time
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from chunklint.config import default_config_yaml
from chunklint.engine import lint
from chunklint.loader import load_chunks
from chunklint.reporter import print_gate_report, print_report, report_json
from chunklint.rules import ALL_RULES
from chunklint.utils.severity import normalize_severity

app = typer.Typer(help="Static analysis for RAG chunks.", no_args_is_help=True)
console = Console()


@app.command()
def scan(
    path: Annotated[Path, typer.Argument(help="JSON or JSONL chunk file to scan.")],
    output_format: Annotated[
        str,
        typer.Option("--format", help="Output format: text or json."),
    ] = "text",
    out: Annotated[
        Optional[Path],
        typer.Option("--out", help="Write JSON report to a file."),
    ] = None,
    fail_on: Annotated[
        Optional[str],
        typer.Option("--fail-on", help="Fail if issues with this exact severity exist."),
    ] = None,
    config: Annotated[
        Optional[Path],
        typer.Option("--config", help="Path to chunklint.yml."),
    ] = None,
    quiet: Annotated[bool, typer.Option("--quiet", help="Suppress terminal output.")] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", help="Show snippets with grouped examples in text output."),
    ] = False,
    raw: Annotated[
        bool,
        typer.Option("--raw", help="Show raw issue rows after the grouped summary."),
    ] = False,
    examples_per_rule: Annotated[
        int,
        typer.Option("--examples-per-rule", help="Examples to show for each root cause."),
    ] = 3,
    max_issues: Annotated[
        int,
        typer.Option("--max-issues", help="Raw issue rows to show with --raw. Use 0 for all."),
    ] = 20,
) -> None:
    """Scan exported chunks."""
    try:
        output_format = output_format.lower().strip()
        if output_format not in {"text", "json"}:
            raise ValueError("--format must be text or json.")
        selected_severity = normalize_severity(fail_on) if fail_on is not None else None

        chunks = load_chunks(path)
        start = time.perf_counter()
        report = lint(chunks, config_path=config)
        elapsed = time.perf_counter() - start
        json_report = report_json(report)

        if out is not None:
            out.write_text(json_report + "\n")

        if not quiet:
            if output_format == "json":
                console.file.write(json_report + "\n")
                console.file.flush()
            else:
                if selected_severity is not None:
                    print_gate_report(
                        report,
                        selected_severity,
                        console=console,
                        verbose=verbose,
                        raw=raw,
                        examples_per_rule=examples_per_rule,
                        max_issues=max_issues,
                        elapsed=elapsed,
                    )
                else:
                    print_report(
                        report,
                        console=console,
                        verbose=verbose,
                        raw=raw,
                        examples_per_rule=examples_per_rule,
                        max_issues=max_issues,
                        elapsed=elapsed,
                    )

        if selected_severity is not None and _has_issues_with_severity(
            report.issues,
            selected_severity,
        ):
            raise typer.Exit(1)
    except typer.Exit:
        raise
    except ValueError as exc:
        console.print(f"[red]Input/config error:[/red] {exc}")
        raise typer.Exit(2) from exc
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        console.print(f"[red]Internal error:[/red] {exc}")
        raise typer.Exit(3) from exc


@app.command()
def init(
    path: Annotated[Path, typer.Argument(help="Config path to create.")] = Path("chunklint.yml"),
    force: Annotated[bool, typer.Option("--force", help="Overwrite an existing config.")] = False,
) -> None:
    """Create a default config file."""
    if path.exists() and not force:
        console.print(f"[yellow]{path} already exists. Use --force to overwrite.[/yellow]")
        raise typer.Exit(2)
    path.write_text(default_config_yaml())
    console.print(f"Created {path}")


@app.command()
def rules() -> None:
    """List supported rules."""
    table = [
        (rule.id, rule.default_severity, "cross-chunk" if hasattr(rule, "check_all") else "chunk")
        for rule in ALL_RULES
    ]
    for rule_id, severity, scope in table:
        console.print(f"{severity.upper():7} {rule_id:24} {scope}")


def _has_issues_with_severity(issues, severity: str | None) -> bool:
    if severity is None:
        return False
    return any(normalize_severity(issue.severity) == severity for issue in issues)


if __name__ == "__main__":
    app()
