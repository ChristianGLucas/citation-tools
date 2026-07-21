from gen.messages_pb2 import AuthorFieldText, AuthorNameList
from nodes.parse_author_field import parse_author_field
from nodes._test_helpers import FakeAxiomContext


def test_parse_author_field_three_names_mixed_grammar_hand_verified():
    # Hand-verified oracle covering all three BibTeX name forms in one field:
    # "von Last, First", "Last, First" (no von), and "First von Last"
    # (multi-word last name).
    ax = FakeAxiomContext()
    raw = "von Beethoven, Ludwig and Gates, Bill and Jean de La Fontaine"
    result = parse_author_field(ax, AuthorFieldText(raw=raw))
    assert isinstance(result, AuthorNameList)
    assert result.error == ""
    assert len(result.authors) == 3

    a1 = result.authors[0]
    assert a1.von == "von" and a1.last == "Beethoven" and a1.first == "Ludwig" and a1.jr == ""

    a2 = result.authors[1]
    assert a2.von == "" and a2.last == "Gates" and a2.first == "Bill" and a2.jr == ""

    a3 = result.authors[2]
    assert a3.von == "de" and a3.last == "La Fontaine" and a3.first == "Jean" and a3.jr == ""


def test_parse_author_field_jr_suffix():
    ax = FakeAxiomContext()
    result = parse_author_field(ax, AuthorFieldText(raw="King, Jr, Martin Luther"))
    assert result.error == ""
    a = result.authors[0]
    assert a.last == "King" and a.jr == "Jr" and a.first == "Martin Luther"


def test_parse_author_field_empty_yields_empty_list_not_error():
    ax = FakeAxiomContext()
    result = parse_author_field(ax, AuthorFieldText(raw=""))
    assert result.error == ""
    assert list(result.authors) == []


def test_parse_author_field_oversized_returns_structured_error():
    ax = FakeAxiomContext()
    huge = "Smith, John and " * 2_000_000
    result = parse_author_field(ax, AuthorFieldText(raw=huge))
    assert result.error != ""
