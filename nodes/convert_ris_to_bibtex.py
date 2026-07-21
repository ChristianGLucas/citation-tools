from gen.messages_pb2 import RisText, TextResult
from gen.axiom_context import AxiomContext
from nodes.parse_ris import parse_ris
from nodes.serialize_bibtex import serialize_bibtex


def convert_ris_to_bibtex(ax: AxiomContext, input: RisText) -> TextResult:
    """Convert an RIS document straight to BibTeX text: parses with the same
    logic as ParseRis (including cite-key synthesis), then serializes with
    SerializeBibtex. Best-effort, not lossless — RIS type-of-reference codes
    and tags map to their nearest BibTeX counterpart (see the package
    README for the exact mapping table); tags with no BibTeX counterpart
    are dropped. Malformed or oversized input returns a structured error
    rather than crashing.
    """
    parsed = parse_ris(ax, input)
    if parsed.error:
        return TextResult(error=parsed.error)
    return serialize_bibtex(ax, parsed.document)
