from chunklint import lint
from chunklint.config import default_config


def test_starts_mid_sentence_connector():
    report = lint(
        [
            {
                "id": "chunk_2",
                "text": "except enterprise customers may request refunds within 90 days.",
                "source": "refund_policy.md",
                "metadata": {"heading": "Refund Policy"},
            }
        ]
    )

    issue = next(issue for issue in report.issues if issue.rule_id == "starts_mid_sentence")
    assert issue.severity == "high"


def test_connector_start_is_flagged_even_when_first_line_is_short():
    report = lint(
        [
            {
                "id": "chunk_2",
                "text": "except enterprise customers\nmay request refunds within 90 days.",
                "source": "refund_policy.md",
                "metadata": {"heading": "Refund Policy"},
            }
        ]
    )

    assert "starts_mid_sentence" in {issue.rule_id for issue in report.issues}


def test_starts_mid_sentence_continuation_punctuation():
    report = lint(
        [
            {
                "id": "chunk_2",
                "text": ", except enterprise customers may request refunds within 90 days.",
                "source": "refund_policy.md",
                "metadata": {"heading": "Refund Policy"},
            }
        ]
    )

    assert "starts_mid_sentence" in {issue.rule_id for issue in report.issues}


def test_valid_discourse_marker_start_is_not_mid_sentence():
    report = lint(
        [
            {
                "id": "chunk_1",
                "text": "However, customers must submit the refund form within thirty days.",
                "source": "refund_policy.md",
                "metadata": {"heading": "Refund Policy"},
            }
        ]
    )

    assert "starts_mid_sentence" not in {issue.rule_id for issue in report.issues}


def test_lowercase_product_or_tool_start_is_not_mid_sentence():
    report = lint(
        [
            {
                "id": "chunk_1",
                "text": "iPhone setup instructions require the user to open Settings first.",
                "source": "setup.md",
                "metadata": {"heading": "iPhone setup"},
            },
            {
                "id": "chunk_2",
                "text": "npm packages should be pinned before publishing production builds.",
                "source": "setup.md",
                "metadata": {"heading": "Package management"},
            },
        ]
    )

    assert "starts_mid_sentence" not in {issue.rule_id for issue in report.issues}


def test_short_lowercase_heading_is_not_mid_sentence():
    report = lint(
        [
            {
                "id": "chunk_1",
                "text": "installation requirements\nPython 3.10 or newer is required.",
                "source": "setup.md",
                "metadata": {"heading": "Installation"},
            }
        ]
    )

    assert "starts_mid_sentence" not in {issue.rule_id for issue in report.issues}


def test_ends_mid_sentence():
    report = lint(
        [
            {
                "id": "chunk_1",
                "text": "Refunds are allowed when the customer submits the form",
                "source": "refund_policy.md",
                "metadata": {"heading": "Refund Policy"},
            }
        ]
    )

    assert "ends_mid_sentence" in {issue.rule_id for issue in report.issues}


def test_ends_mid_sentence_continuation_punctuation():
    report = lint(
        [
            {
                "id": "chunk_1",
                "text": "Refunds are allowed for customers who submit the required form,",
                "source": "refund_policy.md",
                "metadata": {"heading": "Refund Policy"},
            }
        ]
    )

    assert "ends_mid_sentence" in {issue.rule_id for issue in report.issues}


def test_colon_ending_is_allowed_for_intro_or_label():
    report = lint(
        [
            {
                "id": "chunk_1",
                "text": "Required documents:",
                "source": "refund_policy.md",
                "metadata": {"heading": "Refund Policy"},
            }
        ]
    )

    assert "ends_mid_sentence" not in {issue.rule_id for issue in report.issues}


def test_trailing_connector_word_is_mid_sentence():
    report = lint(
        [
            {
                "id": "chunk_1",
                "text": "Refunds are allowed when customers submit the form and",
                "source": "refund_policy.md",
                "metadata": {"heading": "Refund Policy"},
            }
        ]
    )

    assert "ends_mid_sentence" in {issue.rule_id for issue in report.issues}


def test_start_boundary_words_are_configurable():
    config = default_config()
    config.rules["starts_mid_sentence"].model_extra["connector_words"] = ["meanwhile"]

    report = lint(
        [
            {
                "id": "chunk_1",
                "text": "meanwhile customers are still waiting for approval.",
                "source": "refund_policy.md",
                "metadata": {"heading": "Refund Policy"},
            }
        ],
        config=config,
    )

    assert "starts_mid_sentence" in {issue.rule_id for issue in report.issues}


def test_start_ignore_words_are_configurable():
    config = default_config()
    config.rules["starts_mid_sentence"].model_extra["ignore_start_words"] = ["foobar"]

    report = lint(
        [
            {
                "id": "chunk_1",
                "text": "foobar setup instructions require administrators to rotate credentials.",
                "source": "setup.md",
                "metadata": {"heading": "Foobar setup"},
            }
        ],
        config=config,
    )

    assert "starts_mid_sentence" not in {issue.rule_id for issue in report.issues}


def test_table_start_is_not_mid_sentence():
    report = lint(
        [
            {
                "id": "chunk_1",
                "text": "| Plan | Price |\n| --- | --- |\n| Pro | $29 |",
                "source": "pricing.md",
                "metadata": {"heading": "Pricing"},
            }
        ]
    )

    assert "starts_mid_sentence" not in {issue.rule_id for issue in report.issues}
