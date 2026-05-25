from chunklint import lint


def test_pdf_noise_page_label():
    report = lint(
        [
            {
                "id": "chunk_1",
                "text": "Page 2\nRefund Policy. Customers can request refunds within thirty days.",
                "source": "policy.pdf",
                "metadata": {"heading": "Refunds"},
            }
        ]
    )

    assert "pdf_noise" in {issue.rule_id for issue in report.issues}


def test_pdf_noise_repeated_footer():
    chunks = [
        {
            "id": f"chunk_{index}",
            "text": f"Confidential\nSection {index}. Refund details are listed here.\nConfidential",
            "source": "policy.pdf",
            "metadata": {"heading": "Refunds"},
        }
        for index in range(4)
    ]

    report = lint(chunks)

    assert "pdf_noise" in {issue.rule_id for issue in report.issues}

