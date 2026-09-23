# Bible Reference Normalization Capability

## Purpose

Bible Reference Normalization converts human-written English and Chinese
Bible references into canonical CAIF `BiblePassageReference` objects for
applications, AI agents, and other capabilities.

It supports consistent storage of references and provides structured
book, chapter, and verse information to downstream consumers. Version 0.1
supports the 66 books of the Protestant Bible canon.

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

## Examples

| Input | Meaning after normalization |
| --- | --- |
| `John 3` | The entire third chapter of John |
| `Jn 3:16-18` | John chapter 3, verses 16 through 18 |
| `約三16` | John chapter 3, verse 16 |
| `Jude 5` | Jude chapter 1, verse 5 |
| `Genesis 1-3` | Genesis chapters 1 through 3 |
| `創1-3` | Genesis chapters 1 through 3 |

Ambiguous references must be identified rather than silently guessed.
Unresolved ambiguity in deployed applications requires user clarification.
Invalid references must not be fabricated into valid passages.

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
with specification version `0.1`. This directory currently contains its
defining documentation; implementation and tests are not yet present.
