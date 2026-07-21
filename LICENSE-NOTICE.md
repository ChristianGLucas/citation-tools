# Third-party license notice

This package's own code is MIT-licensed (see `LICENSE`). It wraps two
runtime dependencies pinned in `requirements.txt`:

## rispy 0.10.0

MIT License. Copyright (c) 2024 rispy authors. No further runtime
dependencies. License verified from the package's own `LICENSE` file
(`rispy-0.10.0.dist-info/licenses/LICENSE`).

## bibtexparser 1.4.4

Dual-licensed **at the licensee's choice**: BSD-3-Clause OR GNU LGPL v3
(see the `COPYING` file bundled in the PyPI distribution
`bibtexparser-1.4.4.dist-info/licenses/COPYING`, which states "The code is
distributed under a dual license (at your choice)").

**This package elects the BSD-3-Clause option.** BSD-3-Clause is a
permissive license with no copyleft obligations; electing it is exactly
what "at your choice" dual-licensing is designed to permit. (Note: the
project's `main` branch on GitHub has since relicensed to plain MIT for an
unreleased 2.x rewrite — the PyPI-published 1.4.4 this package pins is
still under the dual BSD-3-Clause/LGPLv3 terms above.)

bibtexparser's only runtime dependency is **pyparsing 3.3.2** (MIT
License, verified from its GitHub `LICENSE` file), also pinned in
`requirements.txt`.

## Safety notes relevant to licensing/execution

Neither library evaluates document content as code. bibtexparser resolves
BibTeX `@string` macros via plain text substitution and captures
`@preamble` blocks as inert strings; nothing in this package or its
dependencies calls `eval`/`exec` on parsed input.
