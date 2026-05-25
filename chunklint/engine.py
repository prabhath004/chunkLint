from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from chunklint.config import ChunkLintConfig, load_config
from chunklint.models import Issue, LintContext, LintReport
from chunklint.normalizer import normalize_chunks
from chunklint.rules import DEFAULT_CROSS_CHUNK_RULES, DEFAULT_RULES
from chunklint.utils.severity import normalize_severity


def lint(
    chunks: Iterable[Any],
    *,
    config: ChunkLintConfig | None = None,
    config_path: str | Path | None = None,
) -> LintReport:
    normalized = normalize_chunks(chunks)
    active_config = config or load_config(config_path)
    context = LintContext(config=active_config)

    issues: list[Issue] = []
    for chunk in normalized:
        for rule in DEFAULT_RULES:
            if active_config.is_rule_enabled(rule.id):
                issues.extend(rule.check(chunk, context))

    for rule in DEFAULT_CROSS_CHUNK_RULES:
        if active_config.is_rule_enabled(rule.id):
            issues.extend(rule.check_all(normalized, context))

    return build_report(len(normalized), issues)


def build_report(chunks_scanned: int, issues: list[Issue]) -> LintReport:
    counts = {"high": 0, "medium": 0, "low": 0}
    for issue in issues:
        counts[normalize_severity(issue.severity)] += 1
    return LintReport(
        chunks_scanned=chunks_scanned,
        issues_found=len(issues),
        high=counts["high"],
        medium=counts["medium"],
        low=counts["low"],
        issues=issues,
    )

