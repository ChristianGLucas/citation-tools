from gen.messages_pb2 import BibtexText, TextResult
from nodes.convert_bibtex_to_ris import convert_bibtex_to_ris
from nodes._test_helpers import FakeAxiomContext


def test_convert_bibtex_to_ris_exact_output():
    # Hand-verified oracle for a full BibTeX -> RIS conversion.
    ax = FakeAxiomContext()
    src = (
        "@article{smith2020, author={Smith, John}, title={A Great Paper}, "
        "journal={J. Ex}, year={2020}, doi={10.1/x}}"
    )
    result = convert_bibtex_to_ris(ax, BibtexText(data=src))
    assert isinstance(result, TextResult)
    assert result.error == ""
    expected = (
        "1.\n"
        "TY  - JOUR\n"
        "AU  - Smith, John\n"
        "TI  - A Great Paper\n"
        "JO  - J. Ex\n"
        "PY  - 2020\n"
        "DO  - 10.1/x\n"
        "ER  - \n"
    )
    assert result.data == expected


def test_convert_bibtex_to_ris_malformed_bibtex_yields_structured_error_or_empty():
    ax = FakeAxiomContext()
    huge = "@misc{x, title={" + ("a" * (6 * 1024 * 1024)) + "}}"
    result = convert_bibtex_to_ris(ax, BibtexText(data=huge))
    assert result.error != ""
