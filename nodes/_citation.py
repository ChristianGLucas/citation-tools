"""Shared BibTeX/RIS helpers for the citation-tools package.

Wraps `bibtexparser` (1.4.4, dual BSD-3-Clause/LGPLv3 — this package elects the
permissive BSD-3-Clause option, see LICENSE-NOTICE.md) for BibTeX and `rispy`
(0.10.0, MIT) for RIS. Neither library evaluates code: bibtexparser resolves
`@string` macros as plain text substitution and captures `@preamble` as an
inert string; nothing here calls eval/exec on document content.

Untrusted-input discipline (this package parses caller-supplied text):
  * `check_bounds` caps RAW text at MAX_TEXT_BYTES and, once parsed, every
    entry-producing path caps at MAX_ENTRIES — both enforced before/while
    building output, never after materializing an unbounded collection.
  * `safe()` converts any parser blow-up (including RecursionError/MemoryError
    from a hostile document) into a structured error instead of a crash.
  * Field values are returned as authored (BibTeX's own outer-brace stripping
    only); no code path interprets a field value as executable.
"""
import re

import bibtexparser
import rispy
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.customization import splitname

# Hard cost bounds on untrusted input, enforced before parsing.
MAX_TEXT_BYTES = 5 * 1024 * 1024      # 5 MB of raw source text
MAX_ENTRIES = 20_000                  # entries processed per document
MAX_NAME_TEXT = 20_000                # bytes for a standalone author-field string
MAX_FIELD_VALUE = 100_000             # bytes for any single field value kept

BIBTEX_TYPES = {
    "article", "book", "inbook", "incollection", "inproceedings", "conference",
    "proceedings", "techreport", "mastersthesis", "phdthesis", "manual",
    "booklet", "unpublished", "online", "electronic", "misc", "patent",
    "periodical", "standard",
}

# Best-effort BibTeX <-> RIS type-of-reference mapping. Not lossless: several
# BibTeX types collapse onto one RIS code and vice versa (documented in the
# package README, not silently claimed to round-trip perfectly).
BIBTEX_TO_RIS_TYPE = {
    "article": "JOUR",
    "book": "BOOK",
    "inbook": "CHAP",
    "incollection": "CHAP",
    "inproceedings": "CPAPER",
    "conference": "CPAPER",
    "proceedings": "CONF",
    "techreport": "RPRT",
    "mastersthesis": "THES",
    "phdthesis": "THES",
    "manual": "STAND",
    "booklet": "PAMP",
    "unpublished": "UNPB",
    "online": "ELEC",
    "electronic": "ELEC",
    "misc": "GEN",
    "patent": "PAT",
    "periodical": "JFULL",
    "standard": "STAND",
}
RIS_TO_BIBTEX_TYPE = {
    "JOUR": "article",
    "JFULL": "periodical",
    "MGZN": "article",
    "NEWS": "article",
    "BOOK": "book",
    "CHAP": "incollection",
    "CPAPER": "inproceedings",
    "CONF": "proceedings",
    "RPRT": "techreport",
    "THES": "phdthesis",
    "STAND": "manual",
    "PAMP": "booklet",
    "UNPB": "unpublished",
    "ELEC": "online",
    "GEN": "misc",
    "PAT": "patent",
    "ADVS": "misc",
    "MANSCPT": "unpublished",
    "WEB": "online",
}

# Canonical field name (this package's `fields{}` key) <-> rispy's pythonic
# field name. Only fields with a reasonably direct counterpart are mapped;
# anything else is dropped on conversion (see README for the full list).
FIELD_TO_RISPY = {
    "title": "title",
    "journal": "journal_name",
    "booktitle": "secondary_title",
    "year": "year",
    "volume": "volume",
    "number": "number",
    "doi": "doi",
    "publisher": "publisher",
    "address": "place_published",
    "issn": "issn",
    "abstract": "abstract",
    "series": "tertiary_title",
    "edition": "edition",
    "language": "language",
    "school": "publisher",
    "institution": "publisher",
    "organization": "publisher",
}
RISPY_TO_FIELD = {v: k for k, v in FIELD_TO_RISPY.items() if k not in
                  ("school", "institution", "organization")}  # publisher wins


def check_text_bounds(data):
    """Raise ValueError if raw text exceeds the byte cap; return it unchanged."""
    if data is None:
        data = ""
    raw = data.encode("utf-8", errors="replace")
    if len(raw) > MAX_TEXT_BYTES:
        raise ValueError(
            f"input exceeds size limit: {len(raw)} bytes > {MAX_TEXT_BYTES} byte cap"
        )
    return data


def safe(fn):
    """Run fn() and return (result, "") or (None, message) on any failure.

    Converts a parser blow-up on hostile input into a structured error
    instead of a node crash. RecursionError/MemoryError caught explicitly.
    """
    try:
        return fn(), ""
    except (RecursionError, MemoryError) as exc:
        return None, f"input too complex to process: {type(exc).__name__}"
    except Exception as exc:  # noqa: BLE001 — deterministic structured error contract
        return None, f"{type(exc).__name__}: {exc}"


def _join(tokens):
    return " ".join(t for t in tokens if t)


def split_person_name(raw):
    """Split one "First von Last" / "von Last, First" / "Last, Jr, First"
    name per BibTeX's name grammar into a (von, last, first, jr) tuple of
    space-joined strings, using bibtexparser's splitname.
    """
    parts = splitname(raw, strict_mode=False)
    return (
        _join(parts.get("von", [])),
        _join(parts.get("last", [])),
        _join(parts.get("first", [])),
        _join(parts.get("jr", [])),
    )


def split_name_list(raw):
    """Split an " and "-joined BibTeX author/editor field into a list of
    (raw_piece, von, last, first, jr) tuples. Bounded to MAX_NAME_TEXT bytes
    and a sane number of names.
    """
    if raw is None:
        raw = ""
    if len(raw.encode("utf-8", errors="replace")) > MAX_NAME_TEXT:
        raise ValueError(
            f"author/editor field exceeds size limit ({MAX_NAME_TEXT} bytes)"
        )
    pieces = [p.strip() for p in re.split(r"\s+\band\b\s+", raw.strip(), flags=re.I) if p.strip()]
    pieces = pieces[:MAX_ENTRIES]
    out = []
    for piece in pieces:
        von, last, first, jr = split_person_name(piece)
        out.append((piece, von, last, first, jr))
    return out


def join_person_name(von, last, first, jr):
    """Render (von, last, first, jr) back into a single BibTeX name string
    in "von Last, Jr, First" form (the unambiguous canonical BibTeX form).
    """
    last_part = f"{von} {last}".strip() if von else last
    if jr:
        return f"{last_part}, {jr}, {first}" if first else f"{last_part}, {jr}"
    if first:
        return f"{last_part}, {first}"
    return last_part


def parse_bibtex_text(data):
    """Parse BibTeX source into (entries, strings, preambles, warnings).

    entries: list of raw bibtexparser dicts (ENTRYTYPE/ID + lowercase fields).
    `@string` macros are resolved to plain text (no code execution);
    `@preamble` blocks are captured as inert strings, never evaluated.
    """
    data = check_text_bounds(data)
    parser = BibTexParser(common_strings=True, interpolate_strings=True)
    parser.customization = None
    parser.ignore_nonstandard_types = False
    db = bibtexparser.loads(data, parser=parser)
    entries = db.entries[:MAX_ENTRIES]
    truncated = len(db.entries) > MAX_ENTRIES

    # Cross-check declared "@type{key," headers against what the parser
    # actually returned, to surface entries it silently dropped/recovered
    # from (bibtexparser resyncs on the next "@" rather than raising).
    declared = []
    for m in re.finditer(r"^\s*@\s*([A-Za-z]+)\s*\{\s*([^\s,}]*)\s*,", data, re.M):
        etype = m.group(1).lower()
        if etype in ("string", "preamble", "comment"):
            continue
        line = data.count("\n", 0, m.start()) + 1
        declared.append((etype, m.group(2), line))

    parsed_keys = {e.get("ID", "") for e in entries}
    warnings = []
    for etype, key, line in declared:
        if key and key not in parsed_keys:
            warnings.append((f"entry '{key}' was declared but could not be fully parsed "
                              "(likely unbalanced braces or an unterminated value)",
                              line, key))
    if truncated:
        warnings.append((f"document has more than {MAX_ENTRIES} entries; extra entries were dropped",
                          0, ""))
    return entries, warnings


def normalize_entry_type(raw):
    t = (raw or "misc").strip().lower()
    return t if t in BIBTEX_TYPES else (t or "misc")


def field_value(v):
    """Truncate an individual field value to MAX_FIELD_VALUE bytes."""
    if v is None:
        return ""
    v = str(v)
    b = v.encode("utf-8", errors="replace")
    if len(b) > MAX_FIELD_VALUE:
        return b[:MAX_FIELD_VALUE].decode("utf-8", errors="ignore")
    return v


RESERVED_BIBTEX_KEYS = {"ENTRYTYPE", "ID", "author", "editor"}


def bibtex_entry_to_fields(entry):
    """Lowercase, bounded field dict from a raw bibtexparser entry (author/
    editor excluded — those become structured PersonName lists elsewhere).
    """
    out = {}
    for k, v in entry.items():
        if k in RESERVED_BIBTEX_KEYS:
            continue
        out[k.lower()] = field_value(v)
    return out


def parse_ris_text(data):
    """Parse RIS source into (entries, warnings) where entries is rispy's
    list of pythonic dicts. Cross-checks TY/ER pair counts against what
    rispy actually returned, since rispy (like bibtexparser) silently drops
    malformed records instead of raising.
    """
    data = check_text_bounds(data)
    entries = rispy.loads(data, skip_unknown_tags=False)
    truncated = len(entries) > MAX_ENTRIES
    entries = entries[:MAX_ENTRIES]

    ty_count = len(re.findall(r"^TY\s{0,2}-", data, re.M))
    warnings = []
    if ty_count > len(entries) and not truncated:
        warnings.append((
            f"document declares {ty_count} TY records but only {len(entries)} parsed "
            "cleanly (likely a missing/misplaced ER tag)", 0, "",
        ))
    if truncated:
        warnings.append((f"document has more than {MAX_ENTRIES} entries; extra entries were dropped",
                          0, ""))
    return entries, warnings


def _split_pages(pages):
    """Split a BibTeX-style pages string ("100--110", "100-110", "100") into
    (start, end); end is "" for a single-page value.
    """
    m = re.match(r"^\s*([A-Za-z0-9]+)\s*-{1,2}\s*([A-Za-z0-9]+)\s*$", pages or "")
    if m:
        return m.group(1), m.group(2)
    return (pages or "").strip(), ""


def ris_entry_to_fields_and_pages(entry):
    """Bounded, canonical fields{} dict from a rispy entry (scalar fields
    only; authors/editors/pages/type are handled separately by the caller).
    """
    out = {}
    for rispy_key, canon_key in RISPY_TO_FIELD.items():
        v = entry.get(rispy_key)
        if v:
            out[canon_key] = field_value(v)
    urls = entry.get("urls") or []
    if urls:
        out["url"] = field_value("; ".join(urls))
    notes = entry.get("notes") or entry.get("notes_abstract") or []
    if isinstance(notes, str):
        notes = [notes]
    if notes:
        out["note"] = field_value("; ".join(notes))
    kws = entry.get("keywords") or []
    if kws:
        out["keywords"] = field_value(", ".join(kws))
    sp, ep = entry.get("start_page", ""), entry.get("end_page", "")
    if sp or ep:
        out["pages"] = f"{sp}--{ep}" if sp and ep else (sp or ep)
    return out


def join_person_name_ris(von, last, first, jr):
    """Render (von, last, first, jr) into RIS's conventional "Last, First"
    author-tag form: the von particle folds into the last-name component;
    a Jr suffix is appended to the given-name component (RIS has no
    dedicated suffix slot).
    """
    last_part = f"{von} {last}".strip() if von else last
    first_part = f"{first} {jr}".strip() if jr else first
    return f"{last_part}, {first_part}" if first_part else last_part


def validate_bibtex_structure(data):
    """Structural (not semantic) BibTeX validation: unbalanced braces and
    entries the parser declared but could not fully recover, each with a
    best-effort source line. This is deliberately a shallow syntax check —
    it does not re-derive BibTeX's grammar, only brace balance and the
    declared-vs-parsed cross-check `parse_bibtex_text` already computes.
    """
    errors = []
    stack = []
    line = 1
    for ch in data:
        if ch == "\n":
            line += 1
        elif ch == "{":
            stack.append(line)
        elif ch == "}":
            if stack:
                stack.pop()
            else:
                errors.append(("unexpected closing brace '}' with no matching '{'", line, ""))
    for opened_at in stack:
        errors.append(("brace '{' opened here was never closed", opened_at, ""))

    entries, warnings = parse_bibtex_text(data)
    for message, wline, key in warnings:
        errors.append((message, wline, key))

    seen = {}
    for e in entries:
        key = e.get("ID", "")
        if key and key in seen:
            errors.append((f"duplicate cite key '{key}'", 0, key))
        seen[key] = True

    return errors, len(entries)


def validate_ris_structure(data):
    """Structural RIS validation: every TY record must be closed by an ER
    before the next TY (or end of document), reported with source lines.
    """
    errors = []
    lines = data.split("\n")
    open_line = None
    for i, l in enumerate(lines, start=1):
        if re.match(r"^TY\s{0,2}-", l):
            if open_line is not None:
                errors.append((f"TY record opened on line {open_line} was never closed with ER", i, ""))
            open_line = i
        elif re.match(r"^ER\s{0,2}-", l):
            if open_line is None:
                errors.append(("ER tag with no matching TY", i, ""))
            open_line = None
    if open_line is not None:
        errors.append((f"TY record opened on line {open_line} was never closed with ER", open_line, ""))

    entries, warnings = parse_ris_text(data)
    for message, wline, key in warnings:
        errors.append((message, wline, key))
    return errors, len(entries)


_RIS_TAG_RE = re.compile(r"^[A-Z][A-Z0-9]\s{0,2}-(\s|$)", re.M)
_BIBTEX_ENTRY_RE = re.compile(r"^\s*@\s*[A-Za-z]+\s*\{", re.M)


def detect_format(data):
    """Heuristically classify raw text as "bibtex", "ris", or "unknown",
    with a confidence in [0, 1]. Looks for RIS's "TY  -" / "ER  -" tag
    lines vs BibTeX's "@type{" entry headers; a document containing neither
    pattern is "unknown" with confidence 0.
    """
    data = check_text_bounds(data)
    has_ty = bool(re.search(r"^TY\s{0,2}-", data, re.M))
    has_er = bool(re.search(r"^ER\s{0,2}-", data, re.M))
    ris_tags = len(_RIS_TAG_RE.findall(data))
    bibtex_entries = len(_BIBTEX_ENTRY_RE.findall(data))

    if bibtex_entries == 0 and ris_tags == 0:
        return "unknown", 0.0
    if has_ty and has_er and ris_tags >= bibtex_entries:
        confidence = min(1.0, 0.6 + 0.1 * min(4, ris_tags))
        return "ris", confidence
    if bibtex_entries > 0:
        confidence = min(1.0, 0.6 + 0.1 * min(4, bibtex_entries))
        return "bibtex", confidence
    if ris_tags > 0:
        return "ris", 0.5
    return "unknown", 0.0


def synthesize_cite_key(entry, used_keys):
    """Build a stable cite key from an RIS entry lacking one: firstauthor's
    last name (lowercased, alnum-only) + year, disambiguated with a/b/c on
    collision within this document.
    """
    for cand in (entry.get("id"), entry.get("accession_number"), entry.get("label")):
        if cand:
            base = re.sub(r"[^A-Za-z0-9]", "", str(cand)) or "entry"
            break
    else:
        authors = entry.get("authors") or []
        last = ""
        if authors:
            _, last, _, _ = split_person_name(authors[0])
        last = re.sub(r"[^A-Za-z0-9]", "", last).lower()
        year = re.sub(r"[^0-9]", "", str(entry.get("year", "")))[:4]
        base = f"{last or 'entry'}{year}"
    key = base
    suffix = 0
    while key in used_keys:
        suffix += 1
        key = f"{base}{chr(96 + suffix)}" if suffix <= 26 else f"{base}{suffix}"
    return key
