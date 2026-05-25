from chunklint import lint


def test_broken_markdown_table():
    report = lint(
        [
            {
                "id": "chunk_3",
                "text": "| Pro | $29 |\n| Enterprise | Contact sales |",
                "source": "pricing.md",
                "metadata": {"heading": "Pricing"},
            }
        ]
    )

    assert "broken_markdown_table" in {issue.rule_id for issue in report.issues}


def test_complete_markdown_table_passes_table_rule():
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

    assert "broken_markdown_table" not in {issue.rule_id for issue in report.issues}

