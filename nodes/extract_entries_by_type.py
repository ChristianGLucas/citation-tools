from gen.messages_pb2 import EntryTypeFilter, CitationDocument
from gen.axiom_context import AxiomContext
from nodes._citation import normalize_entry_type


def extract_entries_by_type(ax: AxiomContext, input: EntryTypeFilter) -> CitationDocument:
    """Filter an already-parsed CitationDocument down to entries whose
    normalized entry_type matches the requested type (e.g. "article",
    "inproceedings"), comparing case-insensitively. An unrecognized or
    unmatched type yields an empty document, not an error — filtering a
    well-formed document is a total operation.
    """
    wanted = normalize_entry_type(input.entry_type)
    kept = [e for e in input.document.entries if normalize_entry_type(e.entry_type) == wanted]
    return CitationDocument(entries=kept)
