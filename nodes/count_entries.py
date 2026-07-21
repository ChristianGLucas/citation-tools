from gen.messages_pb2 import CitationDocument, CountResult
from gen.axiom_context import AxiomContext
from nodes._citation import normalize_entry_type


def count_entries(ax: AxiomContext, input: CitationDocument) -> CountResult:
    """Count the entries in a document, total and broken down by normalized
    entry_type (e.g. {"article": 12, "book": 3}).
    """
    by_type = {}
    for e in input.entries:
        t = normalize_entry_type(e.entry_type)
        by_type[t] = by_type.get(t, 0) + 1
    total = sum(by_type.values())
    return CountResult(total=total, by_type=by_type)
