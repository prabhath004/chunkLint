from __future__ import annotations

from rapidfuzz import fuzz

from chunklint.models import Chunk, Issue, LintContext
from chunklint.rules.base import CrossChunkRule


class NearDuplicateRule(CrossChunkRule):
    id = "near_duplicate"
    default_severity = "low"

    def check_all(self, chunks: list[Chunk], context: LintContext) -> list[Issue]:
        threshold = context.config.thresholds.duplicate_similarity
        if threshold <= 1:
            threshold *= 100
        issues: list[Issue] = []
        normalized = [_normalize(chunk.text) for chunk in chunks]
        for left_index, left_text in enumerate(normalized):
            if not left_text:
                continue
            for right_index in range(left_index + 1, len(chunks)):
                right_text = normalized[right_index]
                if not right_text:
                    continue
                score = fuzz.token_set_ratio(left_text, right_text)
                if score >= threshold:
                    original = chunks[left_index]
                    duplicate = chunks[right_index]
                    issues.append(
                        self.issue(
                            duplicate,
                            context,
                            reason=(
                                f"Chunk is {score / 100:.0%} similar to "
                                f"{original.id or f'chunk #{left_index + 1}'}."
                            ),
                            why_it_matters="Duplicate chunks waste index space and can skew retrieval.",
                            fix="Deduplicate chunks before embedding or adjust the splitter overlap.",
                        )
                    )
                    break
        return issues


def _normalize(text: str) -> str:
    return " ".join((text or "").lower().split())

