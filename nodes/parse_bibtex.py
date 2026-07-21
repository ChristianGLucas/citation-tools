from gen.messages_pb2 import (
    BibtexText, ParseResult, CitationDocument, CitationEntry, PersonName, ParseWarning,
)
from gen.axiom_context import AxiomContext
from nodes._citation import (
    parse_bibtex_text, normalize_entry_type, bibtex_entry_to_fields,
    split_name_list, safe,
)


def _names(raw):
    out = []
    for piece, von, last, first, jr in split_name_list(raw or ""):
        out.append(PersonName(raw=piece, von=von, last=last, first=first, jr=jr))
    return out


def parse_bibtex(ax: AxiomContext, input: BibtexText) -> ParseResult:
    """Parse a BibTeX document into the package's canonical CitationDocument:
    one CitationEntry per @-entry, with entry_type normalized to lowercase,
    the cite key preserved as authored, author/editor fields split into
    structured PersonName parts (von/last/first/jr), and every remaining
    field lowercased into `fields{}`. `@string` macros are resolved as plain
    text substitution; `@preamble` is ignored (never evaluated). Bounded to
    5 MB / 20000 entries; entries the parser could not fully recover from
    unbalanced braces surface as warnings, not silent loss. Malformed or
    oversized input returns a structured error rather than crashing.
    """
    def run():
        entries, raw_warnings = parse_bibtex_text(input.data)
        out_entries = []
        for e in entries:
            out_entries.append(CitationEntry(
                entry_type=normalize_entry_type(e.get("ENTRYTYPE", "")),
                cite_key=e.get("ID", ""),
                authors=_names(e.get("author", "")),
                editors=_names(e.get("editor", "")),
                fields=bibtex_entry_to_fields(e),
            ))
        warnings = [ParseWarning(message=m, line=l, entry_key=k) for m, l, k in raw_warnings]
        return ParseResult(document=CitationDocument(entries=out_entries), warnings=warnings)

    result, err = safe(run)
    return result if not err else ParseResult(error=err)
