from gen.messages_pb2 import RawText, FormatResult
from gen.axiom_context import AxiomContext
from nodes._citation import detect_format as _detect, safe


def detect_format(ax: AxiomContext, input: RawText) -> FormatResult:
    """Guess whether raw text is a BibTeX or RIS document by structural
    signal — RIS's "TY  -"/"ER  -" tag lines vs BibTeX's "@type{" entry
    headers — returning "bibtex", "ris", or "unknown" with a heuristic
    confidence in [0, 1].
    """
    def run():
        fmt, conf = _detect(input.data)
        return FormatResult(format=fmt, confidence=conf)

    result, err = safe(run)
    return result if not err else FormatResult(format="unknown", confidence=0.0, error=err)
