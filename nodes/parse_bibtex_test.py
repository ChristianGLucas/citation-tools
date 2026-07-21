from gen.messages_pb2 import BibtexText, ParseResult
from nodes.parse_bibtex import parse_bibtex
from nodes._test_helpers import FakeAxiomContext


def test_parse_bibtex_von_last_first_name_grammar():
    # Hand-verified oracle: "von Last, First" BibTeX name form.
    ax = FakeAxiomContext()
    src = (
        "@book{beethoven1824,\n"
        "  author = {von Beethoven, Ludwig},\n"
        "  title = {Symphony No. 9},\n"
        "  year = {1824},\n"
        "  publisher = {Schott}\n"
        "}\n"
    )
    result = parse_bibtex(ax, BibtexText(data=src))
    assert isinstance(result, ParseResult)
    assert result.error == ""
    assert len(result.document.entries) == 1
    e = result.document.entries[0]
    assert e.entry_type == "book"
    assert e.cite_key == "beethoven1824"
    assert e.fields["title"] == "Symphony No. 9"
    assert e.fields["year"] == "1824"
    assert e.fields["publisher"] == "Schott"
    assert len(e.authors) == 1
    a = e.authors[0]
    assert a.von == "von"
    assert a.last == "Beethoven"
    assert a.first == "Ludwig"
    assert a.jr == ""


def test_parse_bibtex_last_jr_first_name_grammar():
    # Hand-verified oracle: "Last, Jr, First" BibTeX name form.
    ax = FakeAxiomContext()
    src = (
        "@article{king1963,\n"
        "  author = {King, Jr, Martin Luther},\n"
        "  title = {I Have a Dream},\n"
        "  journal = {Speech},\n"
        "  year = {1963}\n"
        "}\n"
    )
    result = parse_bibtex(ax, BibtexText(data=src))
    assert result.error == ""
    e = result.document.entries[0]
    assert e.entry_type == "article"
    a = e.authors[0]
    assert a.von == ""
    assert a.last == "King"
    assert a.jr == "Jr"
    assert a.first == "Martin Luther"


def test_parse_bibtex_multiple_authors_and_string_macro_and_doi():
    # Hand-verified oracle: two authors joined by " and ", journal resolved
    # from an @string macro (plain text substitution, no code execution).
    ax = FakeAxiomContext()
    src = (
        '@string{jofa = "Journal of Foo"}\n\n'
        "@article{smith2020,\n"
        "  author = {Gates, Bill and van Beethoven, Ludwig},\n"
        "  title = {A Study of Foo},\n"
        "  journal = jofa,\n"
        "  year = {2020},\n"
        "  doi = {10.1234/abcd}\n"
        "}\n"
    )
    result = parse_bibtex(ax, BibtexText(data=src))
    assert result.error == ""
    e = result.document.entries[0]
    assert e.fields["journal"] == "Journal of Foo"
    assert e.fields["doi"] == "10.1234/abcd"
    assert len(e.authors) == 2
    assert e.authors[0].last == "Gates" and e.authors[0].first == "Bill"
    assert e.authors[1].von == "van" and e.authors[1].last == "Beethoven"
    assert e.authors[1].first == "Ludwig"


def test_parse_bibtex_preamble_is_not_executed():
    # @preamble commonly carries a LaTeX snippet; it must be inert, never
    # evaluated, and must not affect entry parsing.
    ax = FakeAxiomContext()
    src = (
        '@preamble{"\\newcommand{\\x}[1]{}"}\n\n'
        "@misc{safe1, title = {Fine}, year = {2020}}\n"
    )
    result = parse_bibtex(ax, BibtexText(data=src))
    assert result.error == ""
    assert len(result.document.entries) == 1
    assert result.document.entries[0].cite_key == "safe1"


def test_parse_bibtex_recovers_good_entries_around_a_malformed_one():
    ax = FakeAxiomContext()
    src = (
        "@article{good1, title={T1}, author={A, B}, year={2020}}\n"
        "@article{bad2, title={Unterminated\n"
        "@article{good3, title={T3}, author={C, D}, year={2021}}\n"
    )
    result = parse_bibtex(ax, BibtexText(data=src))
    assert result.error == ""
    keys = {e.cite_key for e in result.document.entries}
    assert keys == {"good1", "good3"}
    assert any("bad2" in w.entry_key or "bad2" in w.message for w in result.warnings)


def test_parse_bibtex_oversized_input_returns_structured_error():
    ax = FakeAxiomContext()
    huge = "@misc{x, title={" + ("a" * (6 * 1024 * 1024)) + "}}"
    result = parse_bibtex(ax, BibtexText(data=huge))
    assert result.error != ""
    assert len(result.document.entries) == 0
