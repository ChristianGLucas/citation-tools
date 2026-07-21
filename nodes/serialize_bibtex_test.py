from gen.messages_pb2 import CitationDocument, CitationEntry, PersonName, TextResult
from nodes.serialize_bibtex import serialize_bibtex
from nodes._test_helpers import FakeAxiomContext


def test_serialize_bibtex_exact_rendered_text():
    # Hand-verified oracle: exact expected BibTeX text for a known entry,
    # given the package's fixed field order (title, author, journal, year,
    # doi — the subset of DISPLAY_ORDER present here) and 2-space indent.
    ax = FakeAxiomContext()
    doc = CitationDocument(entries=[
        CitationEntry(
            entry_type="article", cite_key="smith2020",
            authors=[PersonName(von="", last="Gates", first="Bill", jr="")],
            fields={"title": "A Study", "journal": "J. Foo", "year": "2020", "doi": "10.1234/abcd"},
        )
    ])
    result = serialize_bibtex(ax, doc)
    assert isinstance(result, TextResult)
    assert result.error == ""
    expected = (
        "@article{smith2020,\n"
        "  title = {A Study},\n"
        "  author = {Gates, Bill},\n"
        "  journal = {J. Foo},\n"
        "  year = {2020},\n"
        "  doi = {10.1234/abcd}\n"
        "}\n"
    )
    assert result.data == expected


def test_serialize_bibtex_renders_von_and_jr_name_parts():
    ax = FakeAxiomContext()
    doc = CitationDocument(entries=[
        CitationEntry(
            entry_type="book", cite_key="b1",
            authors=[
                PersonName(von="van", last="Beethoven", first="Ludwig", jr=""),
                PersonName(von="", last="King", first="Martin Luther", jr="Jr"),
            ],
            fields={"title": "T"},
        )
    ])
    result = serialize_bibtex(ax, doc)
    assert result.error == ""
    assert "author = {van Beethoven, Ludwig and King, Jr, Martin Luther}" in result.data


def test_serialize_bibtex_deterministic_across_calls():
    ax = FakeAxiomContext()
    doc = CitationDocument(entries=[
        CitationEntry(entry_type="misc", cite_key="x1", fields={"title": "T", "note": "N"}),
    ])
    r1 = serialize_bibtex(ax, doc)
    r2 = serialize_bibtex(ax, doc)
    assert r1.data == r2.data and r1.data != ""
