from gen.messages_pb2 import CitationDocument, CiteKeyList
from gen.axiom_context import AxiomContext


def extract_cite_keys(ax: AxiomContext, input: CitationDocument) -> CiteKeyList:
    """Pull every entry's cite key, in document order (including any
    duplicates — this node reports what's there, it does not deduplicate).
    """
    return CiteKeyList(cite_keys=[e.cite_key for e in input.entries])
