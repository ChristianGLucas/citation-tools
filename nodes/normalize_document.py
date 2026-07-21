from gen.messages_pb2 import CitationDocument, CitationEntry, PersonName
from gen.axiom_context import AxiomContext
from nodes._citation import normalize_entry_type


def _clean_name(n):
    return PersonName(
        raw=n.raw.strip(), von=n.von.strip(), last=n.last.strip(),
        first=n.first.strip(), jr=n.jr.strip(),
    )


def normalize_document(ax: AxiomContext, input: CitationDocument) -> CitationDocument:
    """Canonicalize a parsed document for stable, comparable output:
    entry_type lowercased to the standard BibTeX vocabulary, entries
    reordered by cite_key (ties broken by original position), and every
    field/name value whitespace-trimmed. Field ordering itself has no
    canonical form here — `fields{}` is an unordered map; SerializeBibtex
    and SerializeRis are what impose a fixed, deterministic field order on
    rendered text.
    """
    normalized = []
    for e in input.entries:
        fields = {k: v.strip() for k, v in e.fields.items()}
        normalized.append(CitationEntry(
            entry_type=normalize_entry_type(e.entry_type),
            cite_key=e.cite_key.strip(),
            authors=[_clean_name(n) for n in e.authors],
            editors=[_clean_name(n) for n in e.editors],
            fields=fields,
        ))
    normalized.sort(key=lambda e: e.cite_key)
    return CitationDocument(entries=normalized)
