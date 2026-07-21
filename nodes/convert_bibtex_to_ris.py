from gen.messages_pb2 import BibtexText, TextResult
from gen.axiom_context import AxiomContext
from nodes.parse_bibtex import parse_bibtex
from nodes.serialize_ris import serialize_ris


def convert_bibtex_to_ris(ax: AxiomContext, input: BibtexText) -> TextResult:
    """Convert a BibTeX document straight to RIS text: parses with the same
    logic as ParseBibtex, then serializes with SerializeRis. Best-effort,
    not lossless — entry types and fields map to their nearest RIS
    counterpart (see the package README for the exact mapping table);
    fields with no RIS counterpart are dropped. Malformed or oversized
    input returns a structured error rather than crashing.
    """
    parsed = parse_bibtex(ax, input)
    if parsed.error:
        return TextResult(error=parsed.error)
    return serialize_ris(ax, parsed.document)
