from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from chunklint.config import default_config_yaml
from chunklint.engine import lint
from chunklint.loader import load_chunks
from chunklint.reporter import print_report, report_json
from chunklint.rules import ALL_RULES
from chunklint.utils.severity import at_or_above, normalize_severity

app = typer.Typer(help="Static analysis for RAG chunks.", no_args_is_help=True)
console = Console()


@app.command()
def scan(
    path: Annotated[Path, typer.Argument(help="JSON or JSONL chunk file to scan.")],
    output_format: Annotated[
        str,
        typer.Option("--format", help="Output format: text or json."),
    ] = "text",
    out: Annotated[Path | None, typer.Option("--out", help="Write JSON report to a file.")] = None,
    fail_on: Annotated[
        str | None,
        typer.Option("--fail-on", help="Fail if issues at or above severity exist."),
    ] = None,
    config: Annotated[Path | None, typer.Option("--config", help="Path to chunklint.yml.")] = None,
    quiet: Annotated[bool, typer.Option("--quiet", help="Suppress terminal output.")] = False,
) -> None:
    """Scan exported chunks."""
    try:
        output_format = output_format.lower().strip()
        if output_format not in {"text", "json"}:
            raise ValueError("--format must be text or json.")
        if fail_on is not None:
            normalize_severity(fail_on)

        chunks = load_chunks(path)
        report = lint(chunks, config_path=config)
        json_report = report_json(report)

        if out is not None:
            out.write_text(json_report + "\n")

        if not quiet:
            if output_format == "json":
                console.print(json_report)
            else:
                print_report(report, console=console)

        if fail_on and any(at_or_above(issue.severity, fail_on) for issue in report.issues):
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


if __name__ == "__main__":
    app()

