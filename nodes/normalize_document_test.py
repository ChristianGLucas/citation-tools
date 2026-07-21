from gen.messages_pb2 import CitationDocument, CitationEntry, PersonName
from nodes.normalize_document import normalize_document
from nodes._test_helpers import FakeAxiomContext


def test_normalize_document_lowercases_type_trims_and_sorts_by_key():
    ax = FakeAxiomContext()
    doc = CitationDocument(entries=[
        CitationEntry(entry_type="ARTICLE", cite_key="zeta1",
                      fields={"title": "  Z Title  "},
                      authors=[PersonName(raw=" A, B ", last=" A ", first=" B ")]),
        CitationEntry(entry_type="Book", cite_key="alpha1", fields={"title": "A Title"}),
    ])
    result = normalize_document(ax, doc)
    assert isinstance(result, CitationDocument)
    assert [e.cite_key for e in result.entries] == ["alpha1", "zeta1"]
    zeta = result.entries[1]
    assert zeta.entry_type == "article"
    assert zeta.fields["title"] == "Z Title"
    assert zeta.authors[0].last == "A"
    assert zeta.authors[0].first == "B"
    alpha = result.entries[0]
    assert alpha.entry_type == "book"


def test_normalize_document_empty_is_a_noop():
    ax = FakeAxiomContext()
    result = normalize_document(ax, CitationDocument())
    assert list(result.entries) == []
