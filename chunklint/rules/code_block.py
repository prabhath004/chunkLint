from __future__ import annotations

from chunklint.models import Chunk, Issue, LintContext
from chunklint.rules.base import Rule


class BrokenCodeBlockRule(Rule):
    id = "broken_code_block"
    default_severity = "medium"

    def check(self, chunk: Chunk, context: LintContext) -> list[Issue]:
        fence_count = chunk.text.count("```")
        if fence_count == 0 or fence_count % 2 == 0:
            return []
        return [
            self.issue(
                chunk,
                context,
                reason="Chunk has an unclosed markdown code fence.",
                why_it_matters="Broken code fences can corrupt surrounding documentation context.",
                fix="Keep fenced code blocks intact or repeat the opening/closing fence in the chunk.",
            )
        ]

