from __future__ import annotations

import re

from chunklint.models import Chunk, Issue, LintContext
from chunklint.rules.base import Rule
from chunklint.utils.text import (
    is_ignorable_sentence_end,
    is_probably_code_or_table_start,
    looks_like_heading_or_label,
    non_empty_lines,
    strip_leading_markup,
    strip_wrapping_openers,
    word_count,
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

RELATIVE_START_WORDS = {"that", "which", "whose", "whom", "where", "when"}
COORDINATING_START_WORDS = {"and", "but", "or", "nor", "so", "yet"}
SUBORDINATING_START_WORDS = {"although", "because", "except", "though", "unless", "whereas", "while"}
DISCOURSE_MARKERS = {"also", "however", "then", "therefore"}
CONTINUATION_PUNCTUATION = {",", ";", ":", ")", "]", "}", "-", "–", "—"}
END_PUNCTUATION = set(".!?)]}`\"'")
TRAILING_CONTINUATION_WORDS = {
    "and",
    "as",
    "because",
    "but",
    "for",
    "if",
    "nor",
    "or",
    "so",
    "that",
    "then",
    "unless",
    "when",
    "where",
    "which",
    "while",
    "with",
    "yet",
}


class StartsMidSentenceRule(Rule):
    id = "starts_mid_sentence"
    default_severity = "high"

    def check(self, chunk: Chunk, context: LintContext) -> list[Issue]:
        lines = non_empty_lines(chunk.text)
        if not lines or is_probably_code_or_table_start(chunk.text):
            return []
        if looks_like_heading_or_label(lines[0]):
            return []

        text = strip_wrapping_openers(strip_leading_markup(chunk.text))
        if not text:
            return []

        if text[0] in CONTINUATION_PUNCTUATION:
            return [
                self.issue(
                    chunk,
                    context,
                    reason=f'Chunk starts with continuation punctuation "{text[0]}".',
                    why_it_matters="This chunk likely begins after a sentence was already in progress.",
                    fix="Split on sentence boundaries or include overlap from the previous chunk.",
                )
            ]

        match = re.match(r"([A-Za-z][\w'.-]*)", text)
        if match is None:
            return []
        first_word = match.group(1)
        first_word_lower = first_word.lower().strip(".")
        if _is_ignored_start_word(first_word, context):
            return []

        connector_words = set(
            context.config.rule_option(self.id, "connector_words", sorted(CONNECTOR_WORDS))
        )
        next_char = text[match.end() : match.end() + 1]
        if _is_strong_continuation_word(first_word_lower, next_char, connector_words):
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
        if _should_flag_lowercase_start(first_word, text):
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
        lines = non_empty_lines(text)
        if not text or is_ignorable_sentence_end(text) or not lines:
            return []
        if looks_like_heading_or_label(lines[-1]):
            return []
        stripped = text.rstrip()
        if stripped[-1] == ":" and context.config.rule_option(self.id, "allow_colon_endings", True):
            return []
        if stripped[-1] in {",", ";", "-", "–", "—"}:
            return [
                self.issue(
                    chunk,
                    context,
                    reason=f'Chunk ends with continuation punctuation "{stripped[-1]}".',
                    why_it_matters="This chunk likely stops before the sentence or list item finishes.",
                    fix="Split on sentence boundaries or increase chunk overlap.",
                )
            ]
        last_word_match = re.search(r"([A-Za-z][\w'-]*)\W*$", stripped)
        if last_word_match and last_word_match.group(1).lower() in TRAILING_CONTINUATION_WORDS:
            return [
                self.issue(
                    chunk,
                    context,
                    reason=f'Chunk ends with connector word "{last_word_match.group(1).lower()}".',
                    why_it_matters="This chunk likely stops before the sentence finishes.",
                    fix="Split on sentence boundaries or increase chunk overlap.",
                )
            ]
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


def _is_ignored_start_word(first_word: str, context: LintContext) -> bool:
    configured = context.config.rule_option("starts_mid_sentence", "ignore_start_words", [])
    ignored = {str(word).lower() for word in configured}
    normalized = first_word.lower().strip(".")
    if normalized in ignored:
        return True
    # CamelCase, iPhone-style, and versioned tokens are usually product/API names, not fragments.
    if first_word[:1].islower() and any(char.isupper() or char.isdigit() for char in first_word[1:]):
        return True
    return False


def _is_strong_continuation_word(
    first_word_lower: str,
    next_char: str,
    connector_words: set[str],
) -> bool:
    if first_word_lower not in connector_words:
        return False
    if first_word_lower in RELATIVE_START_WORDS | COORDINATING_START_WORDS:
        return True
    if first_word_lower in SUBORDINATING_START_WORDS:
        return first_word_lower == "except" or next_char != ","
    if first_word_lower in DISCOURSE_MARKERS:
        # "However, ..." and "Therefore, ..." are valid sentence starts.
        return next_char != ","
    return True


def _should_flag_lowercase_start(first_word: str, text: str) -> bool:
    if not first_word or not first_word[0].islower():
        return False
    if word_count(text) < 4:
        return False
    if re.match(r"^[a-z][A-Z0-9]", first_word):
        return False
    return True
