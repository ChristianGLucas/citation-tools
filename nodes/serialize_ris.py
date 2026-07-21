import rispy

from gen.messages_pb2 import CitationDocument, TextResult
from gen.axiom_context import AxiomContext
from nodes._citation import (
    FIELD_TO_RISPY, BIBTEX_TO_RIS_TYPE, normalize_entry_type, join_person_name_ris,
    safe, MAX_ENTRIES,
)


def serialize_ris(ax: AxiomContext, input: CitationDocument) -> TextResult:
    """Render a CitationDocument back into RIS text: one TY/ER record per
    CitationEntry, with entry_type mapped to the nearest RIS type-of-
    reference code, PersonName authors/editors rejoined into "Last, First"
    RIS form, a "start--end" pages field split back into SP/EP, and every
    fields{} key with a direct RIS counterpart re-emitted under its tag.
    Deterministic for a given document (rispy's writer emits fields in
    a fixed order); entries beyond the 20000-entry cap are dropped.
    """
    def run():
        rispy_entries = []
        for e in input.entries[:MAX_ENTRIES]:
            r = {"type_of_reference": BIBTEX_TO_RIS_TYPE.get(normalize_entry_type(e.entry_type), "GEN")}
            if e.authors:
                r["authors"] = [join_person_name_ris(n.von, n.last, n.first, n.jr) for n in e.authors]
            if e.editors:
                r["secondary_authors"] = [join_person_name_ris(n.von, n.last, n.first, n.jr) for n in e.editors]
            fields = e.fields
            for canon_key, rispy_key in FIELD_TO_RISPY.items():
                v = fields.get(canon_key)
                if v:
                    r[rispy_key] = v
            if fields.get("url"):
                r["urls"] = [u.strip() for u in fields["url"].split(";") if u.strip()]
            if fields.get("note"):
                r["notes"] = [n.strip() for n in fields["note"].split(";") if n.strip()]
            if fields.get("keywords"):
                r["keywords"] = [k.strip() for k in fields["keywords"].split(",") if k.strip()]
            pages = fields.get("pages", "")
            if pages:
                if "--" in pages:
                    sp, ep = pages.split("--", 1)
                elif "-" in pages:
                    sp, ep = pages.split("-", 1)
                else:
                    sp, ep = pages, ""
                if sp:
                    r["start_page"] = sp
                if ep:
                    r["end_page"] = ep
            rispy_entries.append(r)
        return rispy.dumps(rispy_entries)

    text, err = safe(run)
    return TextResult(data=text) if not err else TextResult(error=err)
