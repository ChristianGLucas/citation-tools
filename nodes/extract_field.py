from gen.messages_pb2 import FieldExtractRequest, FieldExtractResult, FieldValue
from gen.axiom_context import AxiomContext
from nodes._citation import join_person_name


def extract_field(ax: AxiomContext, input: FieldExtractRequest) -> FieldExtractResult:
    """Pull one field's value across every entry in a document — e.g. every
    DOI, every year, every journal. field_name is either a fields{} key
    ("doi", "year", "journal", ...) or the special names "author"/"editor",
    which render each entry's structured names back to "Last, First" text,
    semicolon-joined for multi-author entries. Entries missing the field
    are omitted from the result, not reported with an empty value.
    """
    name = (input.field_name or "").strip().lower()
    values = []
    for e in input.document.entries:
        if name == "author":
            v = "; ".join(join_person_name(n.von, n.last, n.first, n.jr) for n in e.authors)
        elif name == "editor":
            v = "; ".join(join_person_name(n.von, n.last, n.first, n.jr) for n in e.editors)
        else:
            v = e.fields.get(name, "")
        if v:
            values.append(FieldValue(cite_key=e.cite_key, value=v))
    return FieldExtractResult(values=values)
