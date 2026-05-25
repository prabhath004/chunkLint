from __future__ import annotations

from chunklint.models import Chunk, Issue, LintContext
from chunklint.rules.base import Rule


class MissingIdRule(Rule):
    id = "missing_id"
    default_severity = "medium"

    def check(self, chunk: Chunk, context: LintContext) -> list[Issue]:
        if chunk.id:
            return []
        return [
            self.issue(
                chunk,
                context,
                reason="Chunk has no stable ID.",
                why_it_matters="Without stable chunk IDs, debugging and deduping are harder.",
                fix="Generate deterministic IDs using source, index, and a content hash.",
            )
        ]

