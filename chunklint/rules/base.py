from __future__ import annotations

from abc import ABC, abstractmethod

from chunklint.models import Chunk, Issue, LintContext
from chunklint.utils.text import snippet


class Rule(ABC):
    id: str
    default_severity: str

    @abstractmethod
    def check(self, chunk: Chunk, context: LintContext) -> list[Issue]:
        raise NotImplementedError

    def severity(self, context: LintContext) -> str:
        return context.config.severity_for(self.id, self.default_severity)

    def issue(
        self,
        chunk: Chunk,
        context: LintContext,
        reason: str,
        why_it_matters: str,
        fix: str,
        severity: str | None = None,
        issue_snippet: str | None = None,
    ) -> Issue:
        return Issue(
            chunk_id=chunk.id,
            source=chunk.source,
            rule_id=self.id,
            severity=severity or self.severity(context),
            reason=reason,
            why_it_matters=why_it_matters,
            fix=fix,
            snippet=issue_snippet if issue_snippet is not None else snippet(chunk.text),
        )


class CrossChunkRule(ABC):
    id: str
    default_severity: str

    @abstractmethod
    def check_all(self, chunks: list[Chunk], context: LintContext) -> list[Issue]:
        raise NotImplementedError

    def severity(self, context: LintContext) -> str:
        return context.config.severity_for(self.id, self.default_severity)

    def issue(
        self,
        chunk: Chunk,
        context: LintContext,
        reason: str,
        why_it_matters: str,
        fix: str,
        severity: str | None = None,
        issue_snippet: str | None = None,
    ) -> Issue:
        return Issue(
            chunk_id=chunk.id,
            source=chunk.source,
            rule_id=self.id,
            severity=severity or self.severity(context),
            reason=reason,
            why_it_matters=why_it_matters,
            fix=fix,
            snippet=issue_snippet if issue_snippet is not None else snippet(chunk.text),
        )

