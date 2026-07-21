# citation-tools

Composable [Axiom](https://axiom.dev) nodes for **deterministic BibTeX and RIS
citation parsing, serialization, format-conversion, and field-extraction** —
wrapping the MIT-licensed [`rispy`](https://github.com/MrTango/rispy) engine
and [`bibtexparser`](https://github.com/sciunto-org/python-bibtexparser)
(dual BSD-3-Clause/LGPLv3 — this package elects the permissive BSD-3-Clause
option; see `LICENSE-NOTICE.md`). Built for the Axiom marketplace.

Every node is stateless and offline: no DOI resolution, no metadata lookups,
no network calls, no wall-clock, no randomness. Untrusted input is bounded
(5 MB / 20000 entries) before parsing, and malformed input returns a
structured error field instead of crashing.

## The canonical envelope

Most nodes read and/or write a single `CitationDocument` — a list of
`CitationEntry`, each with a normalized lowercase `entry_type` (BibTeX
vocabulary: `article`, `book`, `inproceedings`, ...), a `cite_key`,
structured `authors`/`editors` (`PersonName`: `von`/`last`/`first`/`jr`, per
BibTeX's name grammar), and a `fields{}` map for everything else (title,
journal, year, doi, ...).

## Nodes

| Node | Input → Output | What it does |
|------|----------------|--------------|
| `ParseBibtex` | `BibtexText` → `ParseResult` | Parse BibTeX into a `CitationDocument`, with author/editor name splitting and `@string`/`@preamble` handled safely (never evaluated). |
| `SerializeBibtex` | `CitationDocument` → `TextResult` | Render back to BibTeX with a fixed, deterministic field order. |
| `ParseRis` | `RisText` → `ParseResult` | Parse RIS into a `CitationDocument`, synthesizing a cite key when none is present. |
| `SerializeRis` | `CitationDocument` → `TextResult` | Render back to RIS. |
| `ConvertBibtexToRis` | `BibtexText` → `TextResult` | Parse + re-serialize in one call. Best-effort, not lossless. |
| `ConvertRisToBibtex` | `RisText` → `TextResult` | Parse + re-serialize in one call. Best-effort, not lossless. |
| `ExtractEntriesByType` | `EntryTypeFilter` → `CitationDocument` | Keep only entries of one normalized type. |
| `ExtractField` | `FieldExtractRequest` → `FieldExtractResult` | Pull one field (or `author`/`editor`) across every entry. |
| `ParseAuthorField` | `AuthorFieldText` → `AuthorNameList` | Split a raw " and "-joined name field into structured `PersonName`s, standalone. |
| `CountEntries` | `CitationDocument` → `CountResult` | Total and per-type entry counts. |
| `ValidateDocument` | `ValidateRequest` → `ValidationResult` | Structural syntax check (unbalanced braces / mismatched TY-ER / duplicate keys) with source lines. |
| `DetectFormat` | `RawText` → `FormatResult` | Heuristically classify text as BibTeX, RIS, or unknown. |
| `NormalizeDocument` | `CitationDocument` → `CitationDocument` | Canonicalize type casing, entry order, and whitespace. |
| `ExtractCiteKeys` | `CitationDocument` → `CiteKeyList` | List every cite key in document order. |

## BibTeX ↔ RIS field mapping is best-effort

Several BibTeX entry types collapse onto one RIS type-of-reference code and
vice versa, and only fields with a reasonably direct counterpart are carried
across (`nodes/_citation.py` has the exact tables). Round-tripping through
both formats is not guaranteed to be lossless — treat conversion as a
practical approximation, not a lossless transform.

## What's not covered (by design)

- No DOI/CrossRef/network metadata resolution — this package is purely a
  text-in/structured-or-text-out transform.
- BibTeX math-mode/complex LaTeX macro expansion beyond `@string` — field
  values are returned close to as-authored (BibTeX's outer brace-protection
  on a whole field value is stripped; braces inside a value are left as
  authored).
- Nested/nonstandard RIS tag extensions beyond the standard tag set `rispy`
  recognizes.

## License

MIT for this package's own code (see `LICENSE`). See `LICENSE-NOTICE.md` for
the two runtime dependencies' licenses, including the explicit BSD-3-Clause
election for `bibtexparser`'s dual license.
