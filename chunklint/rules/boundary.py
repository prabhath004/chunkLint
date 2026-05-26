from __future__ import annotations

import re

from chunklint.models import Chunk, Issue, LintContext
from chunklint.rules.base import CrossChunkRule, Rule
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
SUBORDINATING_START_WORDS = {
    "although",
    "because",
    "except",
    "though",
    "unless",
    "whereas",
    "while",
}
DISCOURSE_MARKERS = {"also", "however", "then", "therefore"}
CONTINUATION_PUNCTUATION = {",", ";", ":", ")", "]", "}", "-", "\u2013", "\u2014"}
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
        heading_like = looks_like_heading_or_label(lines[0])

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
        if heading_like:
            return []
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
        if stripped[-1] in {",", ";", "-", "\u2013", "\u2014"}:
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


class BrokenChunkBoundaryRule(CrossChunkRule):
    id = "broken_chunk_boundary"
    default_severity = "high"

    def check_all(self, chunks: list[Chunk], context: LintContext) -> list[Issue]:
        issues: list[Issue] = []
        for index in range(1, len(chunks)):
            previous = chunks[index - 1]
            current = chunks[index]
            if not _looks_like_broken_boundary(previous.text, current.text, context):
                continue
            previous_label = previous.id or previous.source or f"chunk #{index}"
            issues.append(
                self.issue(
                    current,
                    context,
                    reason=f"Chunk appears to continue an unfinished sentence from {previous_label}.",
                    why_it_matters=(
                        "Adjacent chunks split through one sentence, so retrieval may return "
                        "only half of the needed context."
                    ),
                    fix="Use sentence-aware splitting or increase overlap so the boundary keeps a full sentence.",
                    issue_snippet=_boundary_snippet(previous.text, current.text),
                )
            )
        return issues


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


def _looks_like_broken_boundary(previous_text: str, current_text: str, context: LintContext) -> bool:
    previous = previous_text.rstrip()
    current = strip_wrapping_openers(strip_leading_markup(current_text))
    if not previous or not current:
        return False
    previous_lines = non_empty_lines(previous)
    current_lines = non_empty_lines(current)
    if not previous_lines or not current_lines:
        return False
    if looks_like_heading_or_label(current_lines[0]) or is_probably_code_or_table_start(current):
        return False
    if current[0] in CONTINUATION_PUNCTUATION:
        return True

    first_match = re.match(r"([A-Za-z][\w'.-]*)", current)
    if first_match is None:
        return False
    first_word = first_match.group(1)
    if _is_ignored_start_word(first_word, context):
        return False

    first_word_lower = first_word.lower().strip(".")
    connector_words = set(
        context.config.rule_option("starts_mid_sentence", "connector_words", sorted(CONNECTOR_WORDS))
    )
    next_char = current[first_match.end() : first_match.end() + 1]
    starts_like_continuation = _is_strong_continuation_word(
        first_word_lower,
        next_char,
        connector_words,
    ) or _should_flag_lowercase_start(first_word, current)

    return starts_like_continuation and _ends_like_unfinished_sentence(previous)


def _ends_like_unfinished_sentence(text: str) -> bool:
    stripped = text.rstrip()
    if not stripped:
        return False
    if stripped[-1] in {",", ";", "-", "\u2013", "\u2014"}:
        return True
    if stripped[-1] in END_PUNCTUATION:
        return False
    last_word_match = re.search(r"([A-Za-z][\w'-]*)\W*$", stripped)
    if last_word_match and last_word_match.group(1).lower() in TRAILING_CONTINUATION_WORDS:
        return True
    return True


def _boundary_snippet(previous_text: str, current_text: str) -> str:
    previous_tail = " ".join(previous_text.split())[-120:]
    current_head = " ".join(current_text.split())[:120]
    return f"{previous_tail} || {current_head}"
