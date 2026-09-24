# Bible Reference Normalization Capability

## Purpose

Bible Reference Normalization converts human-written English and Chinese
Bible references into canonical CAIF `BiblePassageReference` objects for
applications, AI agents, and other capabilities.

It supports consistent storage of references and provides structured
book, chapter, and verse information to downstream consumers. Version 0.1
uses profile `protestant-66-paratext-english`: the Protestant 66-book canon
with SIL/Paratext English (`ScrVers.English`) versification, restricted to
positive-integer chapter and verse coordinates. English names the
numbering convention, not an input-language restriction.

The capability performs structural normalization only. It does not
interpret Scripture, determine doctrine, or perform exegesis.

## Input and Output

The required input is `raw_reference`, a string containing a Bible
reference. Optional context is described in [SPECIFICATION.md](SPECIFICATION.md).

Successful normalization returns a
[`BiblePassageReference`](../../shared/contracts/BiblePassageReference.schema.json)
object. Normalization preserves the original reference text and maps
recognized English and Chinese book names to the same canonical book
identity.

Canonical book IDs are stable, case-sensitive registry keys using full
English names. Numbered books use an ASCII digit and one space, such as
`1 Samuel`, `1 Corinthians`, and `2 John`. Aliases never rename IDs.

A valid address belongs to this profile's numbering convention; it does
not assert that a translation prints that verse in its main text.
Whole-chapter references retain null verse endpoints and are never
expanded into verse ranges.

## Examples

| Input | Meaning after normalization |
| --- | --- |
| `John 3` | The entire third chapter of John |
| `Jn 3:16-18` | John chapter 3, verses 16 through 18 |
| `約三16` or `约三16` | John chapter 3, verse 16 |
| `Jude 5` | Jude chapter 1, verse 5 |
| `Genesis 1-3` | Genesis chapters 1 through 3 |
| `創1-3` | Genesis chapters 1 through 3 |

Ambiguous references must be identified rather than silently guessed.
Unresolved ambiguity in deployed applications requires user clarification.
Invalid references must not be fabricated into valid passages.

## Aliases and Resources

Accepted aliases use `en`, `zh-Hant`, and `zh-Hans`. Matching follows the
deterministic normalization in `book-aliases.json`: NFC, ASCII whitespace
normalization, and ASCII case folding for English only. Matching retains
all candidate book IDs; entry order never resolves ambiguity.

P0 does not accept `約三` / `约三` as the book `3 John`. Use unambiguous
English or full Chinese names such as `約翰三書` / `约翰三书`.
Bare `約翰` / `约翰` remain deferred. No speculative aliases are implied.

The four JSON resources are authoritative for resource data:

- [canon-profiles.json](resources/canon-profiles.json): profile definition,
  ordered canon membership, and exact resource-version bindings.
- [books.json](resources/books.json): stable canonical identities and source-ID
  mappings, without canon order, membership, or chapter counts.
- [book-aliases.json](resources/book-aliases.json): accepted input names,
  language tags, candidate IDs, matching normalization, and deferred aliases.
- [bible-structure.json](resources/bible-structure.json): complete chapter/verse
  maxima, pinned source provenance, licensing, and cross-validation results.

## Documentation

- [SPECIFICATION.md](SPECIFICATION.md) defines normalization behavior,
  supported inputs, error conditions, and acceptance criteria.
- [SKILL.md](SKILL.md) describes agent-facing use of the capability; it
  does not replace the specification or canonical contract.
- [AGENTS.md](AGENTS.md) provides development instructions and engineering
  boundaries.
- [BiblePassageReference.schema.json](../../shared/contracts/BiblePassageReference.schema.json)
  defines the canonical output structure.

## Implementation Boundaries

This capability is shared across CAIF applications and must not depend
on an individual application, model provider, database, or agent framework.
Implementations may use parsing, lookup tables, language-specific logic,
an LLM, or combinations, provided they conform to the specification.

Invocation adapters such as REST, CLI, MCP, or Agent Skills must preserve
the meaning of the normalized reference and the canonical contract.

P0 excludes verse zero, subverse coordinates, cross-versification
conversion, discontinuous references, multiple passages, cross-book
ranges, whole-book-only references, and `ff`. These forms must not be
silently reinterpreted; see the specification for the precise boundaries.
Additional books in the upstream Paratext data are excluded from P0.

## Governance

Structural normalization normally does not require theological review.
The specification classifies governance for Version 0.1 as `OPTIONAL`.
Changes to supported canon profiles should receive human review because
they alter the capability's domain boundary.

The capability must preserve uncertainty and original reference text.
Any surrounding text supplied for disambiguation remains subject to
applicable privacy and access policies.

## Status

Bible Reference Normalization is a draft capability, version `0.1.0`,
with specification version `0.1`. This directory contains the capability
documentation and approved P0 resources, including the complete 66-book
structure extracted from pinned SIL data and cross-validated against
pinned OpenBible `nlt`. A first deterministic offline Python implementation
and pytest suite are present; broader natural-language interpretation and
invocation adapters remain outside this slice.


## Local Python API

Use Python 3.12 (Unicode 15.0.0, matching the alias resource) from a repository
checkout. No package distribution or CLI is provided yet. Install the runtime
`jsonschema` dependency and test-only `pytest` dependency into the repository's
virtual environment, then run the offline suite:

```bash
.venv/bin/python -m pip install -r capabilities/bible-reference-normalization/requirements.txt
cd capabilities/bible-reference-normalization
PYTHONDONTWRITEBYTECODE=1 ../../.venv/bin/python -m pytest -p no:cacheprovider -q
```

With this capability directory on Python's import path:

```python
from bible_reference_normalization import normalize_reference

reference = normalize_reference("約三16", language="zh")
```

`normalize_reference(raw_reference, *, language=None, canon_profile=None)`
returns a dictionary validated against the existing shared JSON Schema.
Every success includes the selected `canon_profile`, defaults to the approved
P0 profile, and preserves `original_text` exactly. The function reads local
resources on each call. It performs no network access or surrounding-text
inference and does not infer an output language from shared alias spellings.

The implemented grammar covers Arabic chapter/verse coordinates and ranges,
explicit English `chapter N` / `chapter N verse(s) N-N`, Chinese chapter and
verse markers, conventional Chinese numerals from 1 through 199, and the
approved mixed form `約三16` / `约三16`. Bare single-chapter-book verse ranges
are not implemented; use explicit coordinates such as `Jude 1:5-7`.
Non-ASCII punctuation and free-form prose are outside this first grammar.

Failures raise implementation-local subclasses of `NormalizationError`:

- `AmbiguousReference`: multiple supported book candidates or parses remain;
  callers must request clarification, never select by entry order.
- `UnsupportedSyntax`: a recognized book has unsupported, incomplete, or
  deferred syntax, including verse zero. This also covers free-form prose
  whose intended ambiguity cannot be classified by the deterministic grammar.
- `InvalidReference`: no accepted book alias, unsupported profile, invalid
  argument type, nonexistent coordinate, or reversed range.
- `ResourceConfigurationError`: unavailable, malformed, or inconsistently
  versioned resources, incompatible runtime Unicode data, or contract failure.

These distinctions are local Python behavior, not a new CAIF result contract.
They do not exhaustively classify human-language ambiguity. No failure returns
partial coordinates, a status envelope, or a confidence-based guess. The
resources and shared contract are unchanged.
