"""Cover the YAML config loading path that the rest of the test suite ignores."""

from __future__ import annotations

import pytest

from chunklint.config import (
    DEFAULT_RULES,
    ChunkLintConfig,
    default_config,
    default_config_yaml,
    load_config,
)


def test_load_config_returns_defaults_when_no_path_given(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = load_config(None)
    assert isinstance(config, ChunkLintConfig)
    assert config.thresholds.min_words == 30
    assert config.is_rule_enabled("starts_mid_sentence")


def test_load_config_auto_discovers_chunklint_yml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "chunklint.yml").write_text(
        "thresholds:\n  min_words: 80\n",
    )
    config = load_config(None)
    assert config.thresholds.min_words == 80
    assert config.thresholds.max_words == 700


def test_load_config_auto_discovers_chunklint_yaml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "chunklint.yaml").write_text(
        "thresholds:\n  duplicate_similarity: 0.5\n",
    )
    config = load_config(None)
    assert config.thresholds.duplicate_similarity == 0.5


def test_load_config_deep_merges_partial_rule_override(tmp_path):
    config_path = tmp_path / "chunklint.yml"
    config_path.write_text(
        "rules:\n"
        "  too_short:\n"
        "    severity: high\n"
    )
    config = load_config(config_path)
    assert config.severity_for("too_short", "low") == "high"
    assert config.is_rule_enabled("starts_mid_sentence")
    assert config.severity_for("starts_mid_sentence", "high") == "high"


def test_load_config_rejects_invalid_yaml(tmp_path):
    config_path = tmp_path / "chunklint.yml"
    config_path.write_text("thresholds:\n  min_words: [oops\n")
    with pytest.raises(ValueError, match="Invalid YAML"):
        load_config(config_path)


def test_load_config_rejects_missing_file(tmp_path):
    missing = tmp_path / "missing.yml"
    with pytest.raises(ValueError, match="does not exist"):
        load_config(missing)


def test_rule_option_returns_extra_keys(tmp_path):
    config_path = tmp_path / "chunklint.yml"
    config_path.write_text(
        "rules:\n"
        "  starts_mid_sentence:\n"
        "    connector_words:\n"
        "      - moreover\n"
    )
    config = load_config(config_path)
    words = config.rule_option("starts_mid_sentence", "connector_words", [])
    assert "moreover" in words


def test_rule_option_falls_back_to_default_when_rule_absent():
    config = default_config()
    sentinel = object()
    assert config.rule_option("not_a_real_rule", "anything", sentinel) is sentinel


def test_default_config_yaml_round_trips(tmp_path):
    config_path = tmp_path / "chunklint.yml"
    config_path.write_text(default_config_yaml())
    config = load_config(config_path)
    for rule_id in DEFAULT_RULES:
        assert config.is_rule_enabled(rule_id)


def test_disabling_a_rule_takes_effect(tmp_path):
    config_path = tmp_path / "chunklint.yml"
    config_path.write_text(
        "rules:\n"
        "  near_duplicate:\n"
        "    enabled: false\n"
    )
    config = load_config(config_path)
    assert not config.is_rule_enabled("near_duplicate")
    assert config.is_rule_enabled("missing_text")


def test_severity_override_is_normalized(tmp_path):
    config_path = tmp_path / "chunklint.yml"
    config_path.write_text(
        "rules:\n"
        "  missing_id:\n"
        "    severity: HIGH\n"
    )
    config = load_config(config_path)
    assert config.severity_for("missing_id", "medium") == "high"
