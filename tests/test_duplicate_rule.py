from chunklint import lint


def test_near_duplicate_chunks():
    text = (
        "Refund Policy. Customers can request refunds within thirty days when purchases "
        "meet all eligibility requirements."
    )

    report = lint(
        [
            {"id": "a", "text": text, "source": "a.md", "metadata": {"heading": "Refunds"}},
            {
                "id": "b",
                "text": text.replace("thirty", "30"),
                "source": "a.md",
                "metadata": {"heading": "Refunds"},
            },
        ]
    )

    assert "near_duplicate" in {issue.rule_id for issue in report.issues}

