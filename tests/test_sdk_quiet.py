from chunklint import lint
from chunklint.adapters.langchain import lint_documents
from chunklint.adapters.llamaindex import lint_nodes


class FakeDocument:
    id = "doc_1"
    page_content = "except enterprise customers may request refunds within 90 days."
    metadata = {"source": "policy.md"}


class FakeNode:
    node_id = "node_1"
    ref_doc_id = "policy"
    metadata = {}

    def get_content(self):
        return "except enterprise customers may request refunds within 90 days."


def test_lint_does_not_print(capsys):
    report = lint(
        [
            {
                "id": "chunk_1",
                "text": "except enterprise customers may request refunds within 90 days.",
                "source": "policy.md",
                "metadata": {},
            }
        ]
    )

    captured = capsys.readouterr()

    assert report.issues_found > 0
    assert captured.out == ""
    assert captured.err == ""


def test_langchain_adapter_does_not_print(capsys):
    report = lint_documents([FakeDocument()])

    captured = capsys.readouterr()

    assert report.issues_found > 0
    assert captured.out == ""
    assert captured.err == ""


def test_llamaindex_adapter_does_not_print(capsys):
    report = lint_nodes([FakeNode()])

    captured = capsys.readouterr()

    assert report.issues_found > 0
    assert captured.out == ""
    assert captured.err == ""
