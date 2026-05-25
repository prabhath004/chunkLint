from chunklint import lint


def test_broken_code_block():
    report = lint(
        [
            {
                "id": "chunk_1",
                "text": "```python\nprint('hello')",
                "source": "docs.md",
                "metadata": {"heading": "Example"},
            }
        ]
    )

    assert "broken_code_block" in {issue.rule_id for issue in report.issues}

