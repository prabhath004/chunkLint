from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from chunklint.utils.severity import normalize_severity


class Thresholds(BaseModel):
    min_words: int = 30
    max_words: int = 700
    duplicate_similarity: float = 0.92
    max_line_break_ratio: float = 0.35


class RuleConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    enabled: bool = True
    severity: str | None = None


class ChunkLintConfig(BaseModel):
    version: int = 1
    thresholds: Thresholds = Field(default_factory=Thresholds)
    required_metadata: list[str] = Field(default_factory=lambda: ["source"])
    heading_keys: list[str] = Field(
        default_factory=lambda: [
            "heading",
            "title",
            "section",
            "heading_path",
            "document_title",
            "file_name",
            "page_label",
        ]
    )
    rules: dict[str, RuleConfig] = Field(default_factory=dict)

    def is_rule_enabled(self, rule_id: str) -> bool:
        return self.rules.get(rule_id, RuleConfig()).enabled

    def severity_for(self, rule_id: str, default: str) -> str:
        configured = self.rules.get(rule_id, RuleConfig()).severity
        if configured is None:
            return normalize_severity(default)
        return normalize_severity(configured)

    def rule_option(self, rule_id: str, key: str, default: Any) -> Any:
        rule = self.rules.get(rule_id)
        if rule is None:
            return default
        extra = rule.model_extra or {}
        return extra.get(key, default)


DEFAULT_RULES: dict[str, dict[str, Any]] = {
    "missing_text": {"enabled": True, "severity": "high"},
    "missing_id": {"enabled": True, "severity": "medium"},
    "missing_source": {"enabled": True, "severity": "medium"},
    "missing_heading": {"enabled": True, "severity": "medium"},
    "starts_mid_sentence": {
        "enabled": True,
        "severity": "high",
        "connector_words": [
            "also",
            "although",
            "and",
            "because",
            "but",
            "except",
            "however",
            "or",
            "that",
            "then",
            "therefore",
            "which",
        ],
        "ignore_start_words": [
            "api",
            "asyncio",
            "aws",
            "azure",
            "ebay",
            "github",
            "ios",
            "ipad",
            "iphone",
            "javascript",
            "langchain",
            "llamaindex",
            "macos",
            "mongodb",
            "node.js",
            "npm",
            "openai",
            "postgres",
            "pytest",
            "python",
            "qdrant",
            "sqlite",
            "typescript",
            "weaviate",
        ],
    },
    "ends_mid_sentence": {
        "enabled": True,
        "severity": "medium",
        "allow_colon_endings": True,
    },
    "broken_chunk_boundary": {"enabled": True, "severity": "high"},
    "too_short": {"enabled": True, "severity": "low"},
    "too_long": {"enabled": True, "severity": "medium"},
    "broken_markdown_table": {"enabled": True, "severity": "high"},
    "broken_code_block": {"enabled": True, "severity": "medium"},
    "near_duplicate": {"enabled": True, "severity": "low"},
    "pdf_noise": {"enabled": True, "severity": "low"},
}


def default_config() -> ChunkLintConfig:
    return ChunkLintConfig(rules={key: RuleConfig(**value) for key, value in DEFAULT_RULES.items()})


def default_config_dict() -> dict[str, Any]:
    return default_config().model_dump(mode="json", exclude_none=True)


def default_config_yaml() -> str:
    return yaml.safe_dump(default_config_dict(), sort_keys=False)


def load_config(path: str | Path | None = None) -> ChunkLintConfig:
    config = default_config()
    config_path = _resolve_config_path(path)
    if config_path is None:
        return config
    try:
        raw = yaml.safe_load(config_path.read_text()) or {}
    except OSError as exc:
        raise ValueError(f"Could not read config file {config_path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in config file {config_path}: {exc}") from exc
    merged = _deep_merge(config.model_dump(mode="json", exclude_none=True), raw)
    return ChunkLintConfig.model_validate(merged)


def _resolve_config_path(path: str | Path | None) -> Path | None:
    if path is not None:
        resolved = Path(path)
        if not resolved.exists():
            raise ValueError(f"Config file does not exist: {resolved}")
        return resolved
    for candidate in (Path("chunklint.yml"), Path("chunklint.yaml")):
        if candidate.exists():
            return candidate
    return None


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
