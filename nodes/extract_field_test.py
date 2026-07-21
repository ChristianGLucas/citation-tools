from gen.messages_pb2 import FieldExtractRequest, FieldExtractResult, CitationDocument, CitationEntry, PersonName
from nodes.extract_field import extract_field
from nodes._test_helpers import FakeAxiomContext


def _doc():
    return CitationDocument(entries=[
        CitationEntry(entry_type="article", cite_key="a1", fields={"doi": "10.1/a"},
                      authors=[PersonName(last="Gates", first="Bill")]),
        CitationEntry(entry_type="article", cite_key="a2", fields={}),  # no doi
        CitationEntry(entry_type="book", cite_key="b1", fields={"doi": "10.1/b"},
                      authors=[PersonName(last="Doe", first="Jane"), PersonName(von="van", last="Beethoven", first="Ludwig")]),
    ])


def test_extract_field_doi_skips_entries_missing_it():
    ax = FakeAxiomContext()
    result = extract_field(ax, FieldExtractRequest(document=_doc(), field_name="doi"))
    assert isinstance(result, FieldExtractResult)
    got = {(v.cite_key, v.value) for v in result.values}
    assert got == {("a1", "10.1/a"), ("b1", "10.1/b")}


def test_extract_field_author_renders_structured_names():
    ax = FakeAxiomContext()
    result = extract_field(ax, FieldExtractRequest(document=_doc(), field_name="author"))
    got = {v.cite_key: v.value for v in result.values}
    assert got["a1"] == "Gates, Bill"
    assert got["b1"] == "Doe, Jane; van Beethoven, Ludwig"
    assert "a2" not in got
