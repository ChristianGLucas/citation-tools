from gen.messages_pb2 import CitationDocument, CitationEntry, PersonName, TextResult
from nodes.serialize_ris import serialize_ris
from nodes._test_helpers import FakeAxiomContext


def test_serialize_ris_exact_rendered_text():
    # Hand-verified oracle: exact expected RIS text (rispy's writer emits a
    # "N." record-counter header line, then tags in the writer's fixed order).
    ax = FakeAxiomContext()
    doc = CitationDocument(entries=[
        CitationEntry(
            entry_type="article", cite_key="smith2020",
            authors=[PersonName(von="", last="Smith", first="John", jr="")],
            fields={
                "title": "A Great Paper", "journal": "Journal of Examples",
                "year": "2020", "doi": "10.1234/example", "pages": "100--110",
            },
        )
    ])
    result = serialize_ris(ax, doc)
    assert isinstance(result, TextResult)
    assert result.error == ""
    expected = (
        "1.\n"
        "TY  - JOUR\n"
        "AU  - Smith, John\n"
        "TI  - A Great Paper\n"
        "JO  - Journal of Examples\n"
        "PY  - 2020\n"
        "DO  - 10.1234/example\n"
        "SP  - 100\n"
        "EP  - 110\n"
        "ER  - \n"
    )
    assert result.data == expected


def test_serialize_ris_maps_entry_type_and_von_particle():
    ax = FakeAxiomContext()
    doc = CitationDocument(entries=[
        CitationEntry(
            entry_type="inproceedings", cite_key="c1",
            authors=[PersonName(von="van", last="Beethoven", first="Ludwig", jr="")],
            fields={"title": "T"},
        )
    ])
    result = serialize_ris(ax, doc)
    assert result.error == ""
    assert "TY  - CPAPER" in result.data
    assert "AU  - van Beethoven, Ludwig" in result.data


def test_serialize_ris_publisher_precedence_when_multiple_set():
    # Regression: publisher/school/institution/organization all target
    # RIS's single PB tag. publisher must win when more than one is set,
    # not whichever key iterates last.
    ax = FakeAxiomContext()
    doc = CitationDocument(entries=[
        CitationEntry(
            entry_type="techreport", cite_key="t1",
            authors=[PersonName(last="Doe", first="Jane")],
            fields={"publisher": "RealPublisher", "school": "MIT",
                    "organization": "ACM", "institution": "Stanford"},
        )
    ])
    result = serialize_ris(ax, doc)
    assert result.error == ""
    assert "PB  - RealPublisher" in result.data
    assert "MIT" not in result.data
    assert "ACM" not in result.data
    assert "Stanford" not in result.data


def test_serialize_ris_round_trips_through_parse_ris():
    from gen.messages_pb2 import RisText
    from nodes.parse_ris import parse_ris

    ax = FakeAxiomContext()
    doc = CitationDocument(entries=[
        CitationEntry(
            entry_type="book", cite_key="rt1",
            authors=[PersonName(von="", last="Doe", first="Jane", jr="")],
            fields={"title": "Round Trip", "year": "1999", "publisher": "Acme"},
        )
    ])
    rendered = serialize_ris(ax, doc)
    assert rendered.error == ""
    reparsed = parse_ris(ax, RisText(data=rendered.data))
    assert reparsed.error == ""
    assert len(reparsed.document.entries) == 1
    e2 = reparsed.document.entries[0]
    assert e2.entry_type == "book"
    assert e2.fields["title"] == "Round Trip"
    assert e2.fields["year"] == "1999"
    assert e2.fields["publisher"] == "Acme"
    assert e2.authors[0].last == "Doe" and e2.authors[0].first == "Jane"
