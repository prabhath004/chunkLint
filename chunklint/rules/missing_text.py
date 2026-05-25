from __future__ import annotations

from chunklint.models import Chunk, Issue, LintContext
from chunklint.rules.base import Rule


class MissingTextRule(Rule):
    id = "missing_text"
    default_severity = "high"

    def check(self, chunk: Chunk, context: LintContext) -> list[Issue]:
        if chunk.text.strip():
            return []
        return [
            self.issue(
                chunk,
                context,
                reason="Chunk text is empty or whitespace only.",
                why_it_matters="Empty chunks waste embedding calls and cannot help retrieval.",
                fix="Drop empty chunks or fix the loader/splitter that produced them.",
                issue_snippet=None,
            )
        ]

