from __future__ import annotations

import re

WORD_RE = re.compile(r"\b[\w'-]+\b")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
LIST_MARKER_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)")
URL_RE = re.compile(r"https?://\S+$")
HTML_TAG_RE = re.compile(r"^\s*</?[a-zA-Z][^>]*>")
KEY_VALUE_RE = re.compile(r"^\s*[\w .()/-]{1,48}:\s+\S")


def word_count(text: str) -> int:
    return len(WORD_RE.findall(text or ""))


def snippet(text: str, limit: int = 160) -> str | None:
    normalized = " ".join((text or "").split())
    if not normalized:
        return None
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 3].rstrip()}..."


def non_empty_lines(text: str) -> list[str]:
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


def is_markdown_table_separator(line: str) -> bool:
    return TABLE_SEPARATOR_RE.match(line) is not None


def looks_like_table_line(line: str) -> bool:
    return "|" in line.strip()


def starts_like_list_item(line: str) -> bool:
    return LIST_MARKER_RE.match(line) is not None


def looks_like_heading_or_label(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("#"):
        return True
    words = word_count(stripped)
    if words <= 8 and stripped.endswith(":"):
        return True
    if KEY_VALUE_RE.match(stripped):
        return True
    if words <= 8 and not re.search(r"[.!?]", stripped):
        return True
    return False


def is_probably_code_or_table_start(text: str) -> bool:
    lines = non_empty_lines(text)
    if not lines:
        return False
    first = lines[0]
    return (
        first.startswith("```")
        or first.startswith("|")
        or first.startswith("#")
        or HTML_TAG_RE.match(first) is not None
        or starts_like_list_item(first)
        or first.startswith((">", "    "))
    )


def is_ignorable_sentence_end(text: str) -> bool:
    lines = non_empty_lines(text)
    if not lines:
        return True
    last = lines[-1]
    return (
        last.startswith("|")
        or starts_like_list_item(last)
        or last.startswith("```")
        or HTML_TAG_RE.match(last) is not None
        or URL_RE.search(last) is not None
    )


def strip_leading_markup(text: str) -> str:
    stripped = (text or "").lstrip()
    stripped = re.sub(r"^(?:>\s*)+", "", stripped)
    stripped = re.sub(r"^(?:[-*+]\s+|\d+[.)]\s+)", "", stripped)
    return stripped.lstrip()


def strip_wrapping_openers(text: str) -> str:
    return (text or "").lstrip(" \t\r\n\"'([{")
