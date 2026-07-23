# citation-tools

Composable [Axiom](https://axiomide.com) nodes for **deterministic BibTeX and RIS
citation parsing, serialization, format-conversion, and field-extraction** —
wrapping the MIT-licensed [`rispy`](https://github.com/MrTango/rispy) engine
and [`bibtexparser`](https://github.com/sciunto-org/python-bibtexparser)
(dual BSD-3-Clause/LGPLv3 — this package elects the permissive BSD-3-Clause
option; see `LICENSE-NOTICE.md`). Built for the Axiom marketplace.

Every node is stateless and offline: no DOI resolution, no metadata lookups,
no network calls, no wall-clock, no randomness. Untrusted input is bounded
(5 MB / 20000 entries) before parsing, and malformed input returns a
structured error field instead of crashing.

## Use it from your agent or app

Every node in this package is a **live, auto-scaling API endpoint** on the
[Axiom](https://axiomide.com) marketplace — call it from an AI agent or your own
code, with nothing to self-host.

**📦 See it on the marketplace:**
https://dev.axiomide.com/marketplace/christiangeorgelucas/citation-tools@0.1.0

**Hook it up to an AI agent (MCP).** Add Axiom's hosted MCP server to any MCP
client and every node becomes a typed tool your agent can call — search the
catalog, inspect a schema, and invoke it directly.

```bash
# Claude Code
claude mcp add --transport http axiom https://api.axiomide.com/mcp \
  --header "Authorization: Bearer $AXIOM_API_KEY"
```

Claude Desktop, Cursor, or any config-based client:

```json
{
  "mcpServers": {
    "axiom": {
      "type": "http",
      "url": "https://api.axiomide.com/mcp",
      "headers": { "Authorization": "Bearer YOUR_AXIOM_API_KEY" }
    }
  }
}
```

**Call it from the CLI.**

```bash
axiom invoke christiangeorgelucas/citation-tools/ParseBibtex --input '{ ... }'
```

**Call it over HTTP.**

```bash
curl -X POST https://api.axiomide.com/invocations/v1/nodes/christiangeorgelucas/citation-tools/0.1.0/ParseBibtex \
  -H "Authorization: Bearer $AXIOM_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{ ... }'
```

> Input/output schema for each node is on the marketplace page above, or via
> `axiom inspect node christiangeorgelucas/citation-tools/ParseBibtex`.

### Get started free

Install the CLI:

```bash
# macOS / Linux — Homebrew
brew install axiomide/tap/axiom

# macOS / Linux — install script
curl -fsSL https://raw.githubusercontent.com/AxiomIDE/axiom-releases/main/install.sh | sh
```

**Windows:** download the `windows/amd64` `.zip` from the
[releases page](https://github.com/AxiomIDE/axiom-releases/releases), unzip it,
and put `axiom.exe` on your `PATH`.

Then `axiom version` to verify, `axiom login` (GitHub or Google) to authenticate,
and create an API key under **Console → API Keys**. Docs and sign-up at
**[axiomide.com](https://axiomide.com)**.

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
