import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

from gen.messages_pb2 import CitationDocument, TextResult
from gen.axiom_context import AxiomContext
from nodes._citation import join_person_name, normalize_entry_type, safe, MAX_ENTRIES

# Fixed, canonical field order — every serialize call produces the same
# ordering for the same content (a same-input round trip is byte-identical).
DISPLAY_ORDER = [
    "title", "author", "editor", "journal", "booktitle", "year", "month",
    "volume", "number", "pages", "publisher", "address", "edition", "series",
    "chapter", "institution", "organization", "school", "howpublished",
    "note", "doi", "isbn", "issn", "url", "abstract", "keywords", "language",
    "type",
]


def _names_str(names):
    return " and ".join(
        join_person_name(n.von, n.last, n.first, n.jr) for n in names
    )


def serialize_bibtex(ax: AxiomContext, input: CitationDocument) -> TextResult:
    """Render a CitationDocument back into BibTeX text: one @-entry per
    CitationEntry, entry type and cite key as stored, author/editor
    PersonName parts rejoined into "von Last, Jr, First" form, and every
    fields{} entry emitted with a fixed canonical field order (common fields
    first in a stable sequence, then any remaining fields sorted
    alphabetically) so the same document always serializes identically.
    Entries beyond the 20000-entry cap are dropped.
    """
    def run():
        db = BibDatabase()
        raw_entries = []
        for e in input.entries[:MAX_ENTRIES]:
            d = {"ENTRYTYPE": normalize_entry_type(e.entry_type), "ID": e.cite_key or "entry"}
            if e.authors:
                d["author"] = _names_str(e.authors)
            if e.editors:
                d["editor"] = _names_str(e.editors)
            for k in sorted(e.fields.keys()):
                if e.fields[k]:
                    d[k] = e.fields[k]
            raw_entries.append(d)
        db.entries = raw_entries
        writer = BibTexWriter()
        writer.display_order = DISPLAY_ORDER
        writer.order_entries_by = ("ID",)
        writer.indent = "  "
        return bibtexparser.dumps(db, writer)

    text, err = safe(run)
    return TextResult(data=text) if not err else TextResult(error=err)
