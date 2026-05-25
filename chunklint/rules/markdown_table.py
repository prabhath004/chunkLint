from __future__ import annotations

from chunklint.models import Chunk, Issue, LintContext
from chunklint.rules.base import Rule
from chunklint.utils.text import is_markdown_table_separator, looks_like_table_line, non_empty_lines


class BrokenMarkdownTableRule(Rule):
    id = "broken_markdown_table"
    default_severity = "high"

    def check(self, chunk: Chunk, context: LintContext) -> list[Issue]:
        lines = non_empty_lines(chunk.text)
        table_lines = [line for line in lines if looks_like_table_line(line)]
        if len(table_lines) < 2:
            return []
        if any(is_markdown_table_separator(line) for line in table_lines):
            return []
        return [
            self.issue(
                chunk,
                context,
                reason="Table rows found but markdown table header separator is missing.",
                why_it_matters="A table fragment without headers loses column meaning after retrieval.",
                fix="Repeat table headers in every table chunk.",
            )
        ]

