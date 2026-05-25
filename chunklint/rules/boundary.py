from __future__ import annotations

import re

from chunklint.models import Chunk, Issue, LintContext
from chunklint.rules.base import Rule
from chunklint.utils.text import (
    is_ignorable_sentence_end,
    is_probably_code_or_table_start,
    strip_leading_markup,
)

CONNECTOR_WORDS = {
    "except",
    "however",
    "therefore",
    "because",
    "although",
    "which",
    "that",
    "and",
    "but",
    "or",
    "also",
    "then",
}

END_PUNCTUATION = set(".!?)]}`\"'")


class StartsMidSentenceRule(Rule):
    id = "starts_mid_sentence"
    default_severity = "high"

    def check(self, chunk: Chunk, context: LintContext) -> list[Issue]:
        if not chunk.text.strip() or is_probably_code_or_table_start(chunk.text):
            return []
        text = strip_leading_markup(chunk.text)
        match = re.match(r"([A-Za-z][\w'-]*)", text)
        if match is None:
            return []
        first_word = match.group(1)
        first_word_lower = first_word.lower()
        if first_word_lower in CONNECTOR_WORDS:
            return [
                self.issue(
                    chunk,
                    context,
                    reason=f'Chunk starts with connector word "{first_word_lower}".',
                    why_it_matters=(
                        "This chunk likely depends on a previous sentence and may lose the main rule."
                    ),
                    fix="Use sentence-aware splitting or increase overlap.",
                )
            ]
        if first_word[0].islower():
            return [
                self.issue(
                    chunk,
                    context,
                    reason="Chunk starts with a lowercase word.",
                    why_it_matters="A lowercase start often means the chunk begins mid-sentence.",
                    fix="Split on sentence boundaries or include enough overlap from the previous chunk.",
                )
            ]
        return []


class EndsMidSentenceRule(Rule):
    id = "ends_mid_sentence"
    default_severity = "medium"

    def check(self, chunk: Chunk, context: LintContext) -> list[Issue]:
        text = chunk.text.rstrip()
        if not text or is_ignorable_sentence_end(text):
            return []
        if text[-1] in END_PUNCTUATION:
            return []
        return [
            self.issue(
                chunk,
                context,
                reason="Chunk does not end with sentence-ending punctuation.",
                why_it_matters="This chunk may be missing the end of an idea or condition.",
                fix="Use sentence-aware splitting or increase chunk overlap.",
            )
        ]

