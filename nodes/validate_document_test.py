from gen.messages_pb2 import ValidateRequest, ValidationResult
from nodes.validate_document import validate_document
from nodes._test_helpers import FakeAxiomContext


def test_validate_document_valid_bibtex():
    ax = FakeAxiomContext()
    result = validate_document(ax, ValidateRequest(data="@article{a1, title={T}, year={2020}}\n", format="bibtex"))
    assert isinstance(result, ValidationResult)
    assert result.valid is True
    assert result.entry_count == 1
    assert result.detected_format == "bibtex"
    assert list(result.errors) == []


def test_validate_document_unbalanced_braces_reports_line_and_key():
    ax = FakeAxiomContext()
    result = validate_document(ax, ValidateRequest(data="@article{a1, title={Unterminated\n", format="bibtex"))
    assert result.valid is False
    assert result.entry_count == 0
    messages = [e.message for e in result.errors]
    assert any("never closed" in m for m in messages)
    assert any("a1" in e.entry_key for e in result.errors)
    assert all(e.line >= 0 for e in result.errors)


def test_validate_document_duplicate_cite_key():
    ax = FakeAxiomContext()
    result = validate_document(ax, ValidateRequest(
        data="@misc{a1,title={T}}\n@misc{a1,title={T2}}\n", format="bibtex"))
    assert result.valid is False
    assert result.entry_count == 2
    assert any("duplicate cite key 'a1'" in e.message for e in result.errors)


def test_validate_document_ris_missing_er_tag():
    ax = FakeAxiomContext()
    result = validate_document(ax, ValidateRequest(data="TY  - JOUR\nTI  - X\n", format="ris"))
    assert result.valid is False
    assert result.detected_format == "ris"
    assert any("never closed with ER" in e.message and e.line == 1 for e in result.errors)


def test_validate_document_auto_detects_ris_and_bibtex():
    ax = FakeAxiomContext()
    r_ris = validate_document(ax, ValidateRequest(data="TY  - JOUR\nTI  - X\nER  -\n", format="auto"))
    assert r_ris.valid is True and r_ris.detected_format == "ris"

    r_bib = validate_document(ax, ValidateRequest(data="@article{a1, title={T}}\n", format="auto"))
    assert r_bib.valid is True and r_bib.detected_format == "bibtex"


def test_validate_document_unrecognizable_text_is_invalid_unknown():
    ax = FakeAxiomContext()
    result = validate_document(ax, ValidateRequest(data="just some plain text\nwith no structure\n", format="auto"))
    assert result.valid is False
    assert result.detected_format == "unknown"
    assert result.entry_count == 0


def test_validate_document_large_input_does_not_crash():
    ax = FakeAxiomContext()
    huge = "@misc{x,title={" + ("a" * (6 * 1024 * 1024)) + "}}"
    result = validate_document(ax, ValidateRequest(data=huge, format="bibtex"))
    assert isinstance(result, ValidationResult)
    # Balanced braces, single well-formed entry -> parses cleanly even at
    # multi-MB size; no payload size limit is imposed by this node.
    assert result.valid is True
    assert result.entry_count == 1
