from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

JSON_SCHEMA_VERSION = 1


class Chunk(BaseModel):
    id: str | None = None
    text: str = ""
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("text", mode="before")
    @classmethod
    def coerce_text(cls, value: Any) -> str:
        if value is None:
            return ""
        return str(value)

    @field_validator("id", "source", mode="before")
    @classmethod
    def coerce_optional_string(cls, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @field_validator("metadata", mode="before")
    @classmethod
    def coerce_metadata(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        return {"value": value}


class Issue(BaseModel):
    chunk_id: str | None
    source: str | None
    rule_id: str
    severity: str
    reason: str
    why_it_matters: str
    fix: str
    snippet: str | None = None


class LintReport(BaseModel):
    chunks_scanned: int
    issues_found: int
    high: int
    medium: int
    low: int
    issues: list[Issue]

    @property
    def has_high_issues(self) -> bool:
        return self.high > 0

    @property
    def ok(self) -> bool:
        return self.issues_found == 0

    def as_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": JSON_SCHEMA_VERSION,
            "summary": {
                "chunks_scanned": self.chunks_scanned,
                "issues_found": self.issues_found,
                "high": self.high,
                "medium": self.medium,
                "low": self.low,
            },
            "issues": [issue.model_dump() for issue in self.issues],
        }

    def print(self) -> None:
        from chunklint.reporter import print_report

        print_report(self)


class LintContext(BaseModel):
    config: Any

