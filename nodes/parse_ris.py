from gen.messages_pb2 import (
    RisText, ParseResult, CitationDocument, CitationEntry, PersonName, ParseWarning,
)
from gen.axiom_context import AxiomContext
from nodes._citation import (
    parse_ris_text, ris_entry_to_fields_and_pages, synthesize_cite_key,
    split_person_name, RIS_TO_BIBTEX_TYPE, safe,
)


def _names(raw_list):
    out = []
    for raw in raw_list or []:
        von, last, first, jr = split_person_name(raw)
        out.append(PersonName(raw=raw, von=von, last=last, first=first, jr=jr))
    return out


def parse_ris(ax: AxiomContext, input: RisText) -> ParseResult:
    """Parse an RIS document into the package's canonical CitationDocument.
    Each TY/ER record becomes one CitationEntry: the RIS type-of-reference
    code is mapped to the nearest lowercase BibTeX entry type, AU/A2 name
    lists are split into structured PersonName parts, SP/EP are combined
    into a BibTeX-style "start--end" pages field, and the remaining tags
    with a direct counterpart are copied into `fields{}`. RIS has no native
    cite key, so one is synthesized from the ID/AN/LB tag if present,
    otherwise from the first author's last name + year, disambiguated on
    collision. Bounded to 5 MB / 20000 records; malformed or oversized
    input returns a structured error rather than crashing.
    """
    def run():
        entries, raw_warnings = parse_ris_text(input.data)
        out_entries = []
        used_keys = set()
        for e in entries:
            key = synthesize_cite_key(e, used_keys)
            used_keys.add(key)
            out_entries.append(CitationEntry(
                entry_type=RIS_TO_BIBTEX_TYPE.get(e.get("type_of_reference", ""), "misc"),
                cite_key=key,
                authors=_names(e.get("authors")),
                editors=_names(e.get("secondary_authors")),
                fields=ris_entry_to_fields_and_pages(e),
            ))
        warnings = [ParseWarning(message=m, line=l, entry_key=k) for m, l, k in raw_warnings]
        return ParseResult(document=CitationDocument(entries=out_entries), warnings=warnings)

    result, err = safe(run)
    return result if not err else ParseResult(error=err)
