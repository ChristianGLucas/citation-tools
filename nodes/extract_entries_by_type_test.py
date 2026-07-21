from gen.messages_pb2 import EntryTypeFilter, CitationDocument, CitationEntry
from nodes.extract_entries_by_type import extract_entries_by_type
from nodes._test_helpers import FakeAxiomContext


def _doc():
    return CitationDocument(entries=[
        CitationEntry(entry_type="article", cite_key="a1"),
        CitationEntry(entry_type="book", cite_key="b1"),
        CitationEntry(entry_type="article", cite_key="a2"),
        CitationEntry(entry_type="INPROCEEDINGS", cite_key="c1"),
    ])


def test_extract_entries_by_type_keeps_only_matching():
    ax = FakeAxiomContext()
    result = extract_entries_by_type(ax, EntryTypeFilter(document=_doc(), entry_type="article"))
    assert isinstance(result, CitationDocument)
    assert [e.cite_key for e in result.entries] == ["a1", "a2"]


def test_extract_entries_by_type_case_insensitive():
    ax = FakeAxiomContext()
    result = extract_entries_by_type(ax, EntryTypeFilter(document=_doc(), entry_type="InProceedings"))
    assert [e.cite_key for e in result.entries] == ["c1"]


def test_extract_entries_by_type_no_match_yields_empty_not_error():
    ax = FakeAxiomContext()
    result = extract_entries_by_type(ax, EntryTypeFilter(document=_doc(), entry_type="phdthesis"))
    assert list(result.entries) == []
