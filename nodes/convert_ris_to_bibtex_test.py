from gen.messages_pb2 import RisText, TextResult
from nodes.convert_ris_to_bibtex import convert_ris_to_bibtex
from nodes._test_helpers import FakeAxiomContext


def test_convert_ris_to_bibtex_exact_output():
    # Hand-verified oracle for a full RIS -> BibTeX conversion, including
    # the synthesized cite key ("smith2020" — no ID tag in the source).
    ax = FakeAxiomContext()
    src = "TY  - JOUR\nAU  - Smith, John\nTI  - A Great Paper\nJO  - J. Ex\nPY  - 2020\nDO  - 10.1/x\nER  -\n"
    result = convert_ris_to_bibtex(ax, RisText(data=src))
    assert isinstance(result, TextResult)
    assert result.error == ""
    expected = (
        "@article{smith2020,\n"
        "  title = {A Great Paper},\n"
        "  author = {Smith, John},\n"
        "  journal = {J. Ex},\n"
        "  year = {2020},\n"
        "  doi = {10.1/x}\n"
        "}\n"
    )
    assert result.data == expected


def test_convert_ris_to_bibtex_oversized_input_returns_structured_error():
    ax = FakeAxiomContext()
    huge = "TY  - JOUR\nTI  - " + ("a" * (6 * 1024 * 1024)) + "\nER  -\n"
    result = convert_ris_to_bibtex(ax, RisText(data=huge))
    assert result.error != ""
