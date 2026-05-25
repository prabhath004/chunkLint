from __future__ import annotations

import re
from collections import Counter

from chunklint.models import Chunk, Issue, LintContext
from chunklint.rules.base import CrossChunkRule
from chunklint.utils.text import non_empty_lines

PAGE_RE = re.compile(r"^(?:page\s+)?\d+(?:\s+of\s+\d+)?$", re.IGNORECASE)
PAGE_LABEL_RE = re.compile(r"\bpage\s+\d+(?:\s+of\s+\d+)?\b", re.IGNORECASE)
HYPHENATED_RE = re.compile(r"\w-\n\w")


class PdfNoiseRule(CrossChunkRule):
    id = "pdf_noise"
    default_severity = "low"

    def check_all(self, chunks: list[Chunk], context: LintContext) -> list[Issue]:
        issues: list[Issue] = []
        repeated_lines = _repeated_edge_lines(chunks)
        for chunk in chunks:
            text = chunk.text
            lines = non_empty_lines(text)
            if not text.strip():
                continue
            if _has_standalone_page_number(lines):
                issues.append(
                    self.issue(
                        chunk,
                        context,
                        reason="Chunk contains standalone page-number noise.",
                        why_it_matters="PDF page artifacts add low-value tokens and can pollute retrieval.",
                        fix="Strip page numbers during PDF text cleanup.",
                    )
                )
                continue
            if PAGE_LABEL_RE.search(text):
                issues.append(
                    self.issue(
                        chunk,
                        context,
                        reason='Chunk contains repeated "Page X" style text.',
                        why_it_matters="PDF headers and footers are usually not useful retrieval context.",
                        fix="Remove repeated page labels before chunking.",
                    )
                )
                continue
            if HYPHENATED_RE.search(text):
                issues.append(
                    self.issue(
                        chunk,
                        context,
                        reason="Chunk contains PDF line-break hyphenation.",
                        why_it_matters="Hyphenated extraction artifacts can break keyword matching.",
                        fix="Join words split across PDF line breaks before chunking.",
                    )
                )
                continue
            if _line_break_ratio(text) > context.config.thresholds.max_line_break_ratio:
                issues.append(
                    self.issue(
                        chunk,
                        context,
                        reason="Chunk has an unusually high line-break ratio.",
                        why_it_matters="Excess line breaks often indicate poor PDF extraction.",
                        fix="Normalize whitespace and remove layout artifacts before splitting.",
                    )
                )
                continue
            repeated = next((line for line in lines if line in repeated_lines), None)
            if repeated:
                issues.append(
                    self.issue(
                        chunk,
                        context,
                        reason=f'Repeated header/footer line found: "{repeated}".',
                        why_it_matters="Repeated headers and footers can dominate retrieval matches.",
                        fix="Strip repeated headers and footers before chunking.",
                    )
                )
        return issues


def _has_standalone_page_number(lines: list[str]) -> bool:
    return any(PAGE_RE.match(line) is not None for line in lines)


def _line_break_ratio(text: str) -> float:
    stripped = text.strip()
    if not stripped:
        return 0
    return text.count("\n") / max(len(stripped), 1)


def _repeated_edge_lines(chunks: list[Chunk]) -> set[str]:
    candidates: list[str] = []
    for chunk in chunks:
        lines = non_empty_lines(chunk.text)
        if not lines:
            continue
        candidates.extend([lines[0], lines[-1]])
    counts = Counter(line for line in candidates if 4 <= len(line) <= 120)
    if len(chunks) < 3:
        return set()
    minimum = max(3, int(len(chunks) * 0.3))
    return {line for line, count in counts.items() if count >= minimum}

