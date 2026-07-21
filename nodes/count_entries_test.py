from gen.messages_pb2 import CitationDocument, CitationEntry, CountResult
from nodes.count_entries import count_entries
from nodes._test_helpers import FakeAxiomContext


def test_count_entries_totals_and_by_type():
    ax = FakeAxiomContext()
    doc = CitationDocument(entries=[
        CitationEntry(entry_type="article", cite_key="a1"),
        CitationEntry(entry_type="article", cite_key="a2"),
        CitationEntry(entry_type="book", cite_key="b1"),
    ])
    result = count_entries(ax, doc)
    assert isinstance(result, CountResult)
    assert result.total == 3
    assert dict(result.by_type) == {"article": 2, "book": 1}


def test_count_entries_empty_document():
    ax = FakeAxiomContext()
    result = count_entries(ax, CitationDocument())
    assert result.total == 0
    assert dict(result.by_type) == {}
