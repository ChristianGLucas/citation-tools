from gen.messages_pb2 import RisText, ParseResult
from nodes.parse_ris import parse_ris
from nodes._test_helpers import FakeAxiomContext

ORACLE_RIS = """TY  - JOUR
AU  - Smith, John
AU  - van Beethoven, Ludwig
TI  - A Great Paper
JO  - Journal of Examples
PY  - 2020
VL  - 10
IS  - 2
SP  - 100
EP  - 110
DO  - 10.1234/example
UR  - https://example.com
AB  - This is an abstract.
KW  - keyword1
KW  - keyword2
ER  -

"""


def test_parse_ris_full_record_hand_verified_oracle():
    ax = FakeAxiomContext()
    result = parse_ris(ax, RisText(data=ORACLE_RIS))
    assert isinstance(result, ParseResult)
    assert result.error == ""
    assert len(result.document.entries) == 1
    e = result.document.entries[0]

    # entry_type: RIS "JOUR" maps to BibTeX "article".
    assert e.entry_type == "article"
    # no ID/AN/LB tag present -> synthesized from first author + year.
    assert e.cite_key == "smith2020"

    assert len(e.authors) == 2
    assert e.authors[0].last == "Smith" and e.authors[0].first == "John" and e.authors[0].von == ""
    assert e.authors[1].von == "van" and e.authors[1].last == "Beethoven" and e.authors[1].first == "Ludwig"

    assert e.fields["title"] == "A Great Paper"
    assert e.fields["journal"] == "Journal of Examples"
    assert e.fields["year"] == "2020"
    assert e.fields["volume"] == "10"
    assert e.fields["number"] == "2"
    assert e.fields["pages"] == "100--110"
    assert e.fields["doi"] == "10.1234/example"
    assert e.fields["url"] == "https://example.com"
    assert e.fields["abstract"] == "This is an abstract."
    assert e.fields["keywords"] == "keyword1, keyword2"


def test_parse_ris_synthesizes_distinct_keys_on_collision():
    ax = FakeAxiomContext()
    src = (
        "TY  - JOUR\nAU  - Lee, Ann\nPY  - 2021\nTI  - First\nER  -\n\n"
        "TY  - JOUR\nAU  - Lee, Ann\nPY  - 2021\nTI  - Second\nER  -\n\n"
    )
    result = parse_ris(ax, RisText(data=src))
    keys = [e.cite_key for e in result.document.entries]
    assert keys[0] == "lee2021"
    assert keys[1] == "lee2021a"
    assert keys[0] != keys[1]


def test_parse_ris_large_input_does_not_crash():
    ax = FakeAxiomContext()
    huge = "TY  - JOUR\nTI  - " + ("a" * (6 * 1024 * 1024)) + "\nER  -\n"
    result = parse_ris(ax, RisText(data=huge))
    # Well-formed single record -> parses cleanly even at multi-MB size; no
    # payload size limit is imposed by this node.
    assert result.error == ""
    assert len(result.document.entries) == 1
