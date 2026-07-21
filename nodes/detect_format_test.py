from gen.messages_pb2 import RawText, FormatResult
from nodes.detect_format import detect_format
from nodes._test_helpers import FakeAxiomContext


def test_detect_format_bibtex():
    ax = FakeAxiomContext()
    result = detect_format(ax, RawText(data="@article{a1, title={T}, year={2020}}\n"))
    assert isinstance(result, FormatResult)
    assert result.format == "bibtex"
    assert result.confidence > 0.5
    assert result.error == ""


def test_detect_format_ris():
    ax = FakeAxiomContext()
    result = detect_format(ax, RawText(data="TY  - JOUR\nTI  - X\nER  -\n"))
    assert result.format == "ris"
    assert result.confidence > 0.5


def test_detect_format_unknown_for_plain_text():
    ax = FakeAxiomContext()
    result = detect_format(ax, RawText(data="This is just an email, not a citation file."))
    assert result.format == "unknown"
    assert result.confidence == 0.0


def test_detect_format_oversized_returns_error():
    ax = FakeAxiomContext()
    huge = "@misc{x," + ("a" * (6 * 1024 * 1024))
    result = detect_format(ax, RawText(data=huge))
    assert result.error != ""
