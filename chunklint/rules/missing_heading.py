from __future__ import annotations

from chunklint.models import Chunk, Issue, LintContext
from chunklint.rules.base import Rule
from chunklint.utils.metadata import has_heading_metadata


class MissingHeadingRule(Rule):
    id = "missing_heading"
    default_severity = "medium"

    def check(self, chunk: Chunk, context: LintContext) -> list[Issue]:
        if has_heading_metadata(chunk.metadata, context.config.heading_keys):
            return []
        return [
            self.issue(
                chunk,
                context,
                reason="Chunk has no heading/title metadata.",
                why_it_matters="Chunks without section context are harder to retrieve and explain.",
                fix="Add heading, section, title, document_title, or heading_path metadata.",
            )
        ]

