from chunklint import lint


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

