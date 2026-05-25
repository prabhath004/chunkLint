from chunklint import lint


LONG_TEXT = (
    "Refund Policy. Customers can request refunds within thirty days when purchases meet "
    "the eligibility requirements listed in the policy document. Support teams should "
    "verify the original purchase date, account status, and product tier before issuing "
    "refunds."
)


def test_missing_text_is_high():
    report = lint([{"id": "empty", "text": "", "source": "a.md", "metadata": {"heading": "A"}}])

    assert "missing_text" in {issue.rule_id for issue in report.issues}
    assert report.high >= 1


def test_missing_id_source_and_heading_are_reported():
    report = lint([{"text": LONG_TEXT, "metadata": {}}])

    rule_ids = {issue.rule_id for issue in report.issues}
    assert {"missing_id", "missing_source", "missing_heading"}.issubset(rule_ids)


def test_valid_metadata_avoids_missing_source_and_heading():
    report = lint(
        [
            {
                "id": "chunk_1",
                "text": LONG_TEXT,
                "source": "policy.md",
                "metadata": {"heading": "Refund Policy"},
            }
        ]
    )

    rule_ids = {issue.rule_id for issue in report.issues}
    assert "missing_source" not in rule_ids
    assert "missing_heading" not in rule_ids

