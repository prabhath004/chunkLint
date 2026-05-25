from chunklint.adapters.langchain import export_documents, lint_documents
from chunklint.adapters.llamaindex import export_nodes, lint_nodes


class FakeDocument:
    id = "doc_1"
    page_content = "Refund Policy. Customers can request refunds within thirty days."
    metadata = {"source": "policy.md", "heading": "Refund Policy"}


class FakeNode:
    node_id = "node_1"
    ref_doc_id = "policy"
    metadata = {"heading": "Refund Policy"}

    def get_content(self):
        return "Refund Policy. Customers can request refunds within thirty days."


def test_langchain_adapter_lints_documents():
    report = lint_documents([FakeDocument()])

    assert report.chunks_scanned == 1


def test_langchain_adapter_exports_documents(tmp_path):
    path = tmp_path / "chunks.json"

    export_documents([FakeDocument()], path)

    assert "doc_1" in path.read_text()


def test_llamaindex_adapter_lints_nodes():
    report = lint_nodes([FakeNode()])

    assert report.chunks_scanned == 1


def test_llamaindex_adapter_exports_nodes(tmp_path):
    path = tmp_path / "chunks.json"

    export_nodes([FakeNode()], path)

    assert "node_1" in path.read_text()

