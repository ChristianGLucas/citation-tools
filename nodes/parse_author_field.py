from gen.messages_pb2 import AuthorFieldText, AuthorNameList, PersonName
from gen.axiom_context import AxiomContext
from nodes._citation import split_name_list, safe


def parse_author_field(ax: AxiomContext, input: AuthorFieldText) -> AuthorNameList:
    """Split a raw BibTeX author/editor field string into structured names
    per BibTeX's name grammar, independent of a full document parse —
    handles "von Last, First" (e.g. "van Beethoven, Ludwig"), "Last, Jr,
    First" (e.g. "King, Jr, Martin Luther"), and plain "First von Last"
    forms, with multiple names joined by " and ". Bounded to 20000 bytes;
    oversized or unparseable input returns a structured error rather than
    crashing.
    """
    def run():
        out = []
        for piece, von, last, first, jr in split_name_list(input.raw):
            out.append(PersonName(raw=piece, von=von, last=last, first=first, jr=jr))
        return out

    names, err = safe(run)
    return AuthorNameList(authors=names) if not err else AuthorNameList(error=err)
