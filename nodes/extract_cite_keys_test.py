from gen.messages_pb2 import CitationDocument, CitationEntry, CiteKeyList
from nodes.extract_cite_keys import extract_cite_keys
from nodes._test_helpers import FakeAxiomContext


def test_extract_cite_keys_preserves_order_and_duplicates():
    ax = FakeAxiomContext()
    doc = CitationDocument(entries=[
        CitationEntry(cite_key="b1"), CitationEntry(cite_key="a1"), CitationEntry(cite_key="b1"),
    ])
    result = extract_cite_keys(ax, doc)
    assert isinstance(result, CiteKeyList)
    assert list(result.cite_keys) == ["b1", "a1", "b1"]


def test_extract_cite_keys_empty_document():
    ax = FakeAxiomContext()
    result = extract_cite_keys(ax, CitationDocument())
    assert list(result.cite_keys) == []
