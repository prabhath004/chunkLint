from __future__ import annotations

from chunklint.models import Chunk, Issue, LintContext
from chunklint.rules.base import Rule
from chunklint.utils.metadata import source_from_metadata


class MissingSourceRule(Rule):
    id = "missing_source"
    default_severity = "medium"

    def check(self, chunk: Chunk, context: LintContext) -> list[Issue]:
        if chunk.source or source_from_metadata(chunk.metadata):
            return []
        return [
            self.issue(
                chunk,
                context,
                reason="Chunk has no source file, document, or page reference.",
                why_it_matters="If this chunk causes a bad answer, it cannot be traced back.",
                fix="Add source metadata such as source, file_name, path, document_id, or page.",
            )
        ]

