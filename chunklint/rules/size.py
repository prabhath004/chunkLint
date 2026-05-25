from __future__ import annotations

from chunklint.models import Chunk, Issue, LintContext
from chunklint.rules.base import Rule
from chunklint.utils.metadata import has_heading_metadata
from chunklint.utils.severity import max_severity
from chunklint.utils.text import word_count


class TooShortRule(Rule):
    id = "too_short"
    default_severity = "low"

    def check(self, chunk: Chunk, context: LintContext) -> list[Issue]:
        if not chunk.text.strip():
            return []
        count = word_count(chunk.text)
        if count >= context.config.thresholds.min_words:
            return []
        severity = self.severity(context)
        if not has_heading_metadata(chunk.metadata, context.config.heading_keys):
            severity = max_severity(severity, "medium")
        return [
            self.issue(
                chunk,
                context,
                reason=f"Chunk has only {count} words.",
                why_it_matters="Tiny chunks often lack enough context to answer questions reliably.",
                fix="Merge with nearby context or include heading/table context.",
                severity=severity,
            )
        ]


class TooLongRule(Rule):
    id = "too_long"
    default_severity = "medium"

    def check(self, chunk: Chunk, context: LintContext) -> list[Issue]:
        count = word_count(chunk.text)
        if count <= context.config.thresholds.max_words:
            return []
        return [
            self.issue(
                chunk,
                context,
                reason=f"Chunk has {count} words.",
                why_it_matters="Huge chunks can mix topics and dilute retrieval relevance.",
                fix="Reduce chunk size or split by section/sentence boundaries.",
            )
        ]

