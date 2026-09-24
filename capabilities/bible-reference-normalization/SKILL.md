---
name: bible-reference-normalization
description: >
  Converts informal or partially structured Scripture references into
  the canonical CAIF BiblePassageReference contract.
version: 0.1.0
status: draft
---

# Bible Reference Normalization Skill

## Purpose

Use this skill to convert user-entered, document-extracted, or
agent-generated Scripture references into canonical CAIF
BiblePassageReference objects.

Examples include:

- "John 3:16"
- "Jn 3:16"
- "John chapter 3 verses 16-18"
- "約翰福音三章十六節"
- "1 Cor 13"
- "Romans 8:28-30"

## When to Use

Use this capability when:

- a Scripture reference must be stored consistently;
- a downstream capability requires BiblePassageReference;
- references from different documents or languages must be normalized;
- a retrieval capability needs structured book/chapter/verse information.

## Inputs

The primary input is:

    raw_reference: string

Optional inputs may include:

    language
    canon_profile
    surrounding_text

For P0 v0.1, omitted `canon_profile` defaults to
`protestant-66-paratext-english`: the Protestant 66-book canon and the
positive-integer subset of SIL/Paratext English (`ScrVers.English`).
English identifies the numbering convention, not an input-language limit.
`canon_profile` covers both; no separate numbering profile is defined yet.

Accepted alias tags are `en`, `zh-Hant`, and `zh-Hans`. A supplied tag
selects that alias language; a broad `zh` hint searches both Chinese tags.
Unknown language searches all three. Shared spellings do not establish script.

## Outputs

On successful normalization, return:

    BiblePassageReference

The output MUST conform to the canonical schema located at:

    shared/contracts/BiblePassageReference.schema.json

The object represents exactly one contiguous inclusive passage within
one book. Required fields are `schema_version` (`"1.0"`), `book`,
`chapter_start`, `verse_start`, `chapter_end`, `verse_end`, and
`original_text`. The old `chapter` field is not supported.

`book` is a stable, case-sensitive key from `books.json`, using full
English names. Numbered IDs use an ASCII digit and one space, such as
`1 Samuel`, `1 Corinthians`, and `2 John`; `Song of Songs` retains spaces.
Aliases do not rename these IDs.

Chapter endpoints are positive integers, never null. Verse endpoints
must both be positive integers or both be null. Null means complete
chapter(s), never unknown or inferred verses. A single chapter repeats
its chapter number; a single verse repeats both chapter and verse
coordinates. All endpoints are inclusive. Whole-chapter and chapter-range
references must retain null verse endpoints, never expand to verse ranges.

The contract is success-only: do not add ambiguity, error, or status
fields or return partial objects for non-success outcomes. No separate
normalization-result contract is defined yet.

## Behavior

The capability should:

1. recognize common Biblical book names and abbreviations;
2. normalize book identity;
3. extract chapter numbers;
4. extract verse ranges within or across chapters and complete chapter ranges;
5. preserve the supplied reference exactly in `original_text`;
6. indicate ambiguity rather than guessing when interpretation is uncertain.

For single-chapter books, a bare number means a verse: `Jude 5` is
`Jude 1:5`. Apply this rule to all supported single-chapter books.
An explicit chapter marker denotes a whole chapter.

Schema validation checks structure, including paired verse endpoint
types. Capability behavior and tests check supported book identities,
actual chapter/verse existence, range ordering, and ambiguity. Across
chapters, the ending verse number may be smaller than the starting one.

Follow the deterministic matching rules in `book-aliases.json`: NFC on
book tokens, collapse and trim ASCII whitespace (U+0009 through U+000D
and U+0020), then fold ASCII A-Z for `en` only. Do not remove punctuation,
delete internal spaces, convert scripts, interpret Roman numerals, or
alter `original_text` during alias matching. Union and deduplicate all
matching candidate IDs; multiple candidates require clarification.

`約三16` and `约三16` mean `John 3:16`. Do not accept `約三` / `约三`
as book aliases for `3 John`. Use approved English or full Chinese names,
such as `約翰三書` / `约翰三书`, for that book. Bare `約翰` / `约翰`
remain deferred. Do not invent aliases or use longest-prefix matching to
override these reference semantics.

A valid address is valid under the selected profile, regardless of whether
a translation prints that verse in its main text. `verse_counts` means
every positive integer from 1 through the stored maximum is valid.

## Resources

The JSON resources are authoritative for data; do not reproduce their
complete contents in prompts or maintain alternative tables.

- [canon-profiles.json](resources/canon-profiles.json): profile definition,
  ordered canon membership, and exact resource-version bindings.
- [books.json](resources/books.json): stable canonical identities and source-ID
  mappings, without canon order, membership, or chapter counts.
- [book-aliases.json](resources/book-aliases.json): accepted input names,
  language tags, candidate IDs, matching normalization, and deferred aliases.
- [bible-structure.json](resources/bible-structure.json): complete chapter/verse
  maxima, pinned source provenance, licensing, and cross-validation results.

Use the profile's exact version bindings and the structural provenance.
The structure derives from pinned SIL data and is cross-validated against
pinned OpenBible `nlt`. Chapter count and single-chapter status come from
complete structure arrays. Missing resources are operational errors, not
invalid user references.

## Do Not Use

Do not use this capability to:

- interpret the theological meaning of a passage;
- determine doctrine;
- generate exegesis;
- decide whether a Biblical interpretation is correct.

This capability normalizes references only.

The v0.1 canonical representation excludes discontinuous references
(`John 3:16,18`), multiple passages (`John 3; Romans 8`), cross-book
ranges, whole-book-only references, `ff`, verse zero, and subverse notation
such as `16a`, unless separately resolved by future specifications.
P0 does not perform cross-versification conversion or include additional
books present in the upstream Paratext data. Do not silently reinterpret
these forms to produce a successful object.


## Uncertainty

If more than one interpretation is plausible, explicitly identify the
ambiguity outside `BiblePassageReference` rather than silently selecting
one. In deployed applications, request user clarification. Non-success
result representation is deferred; confidence metadata does not make an
unresolved reference a successful normalization.

Example:

    "John 3"

means the whole chapter and is valid.

But:

    "John three sixteen eighteen"

may require interpretation depending on context.

## Governance

This capability normally requires no theological governance because it
performs structural normalization rather than theological interpretation.

However, canon-specific book naming or numbering differences should be
preserved explicitly rather than silently overwritten.

## Example

Input:

    "Jn 3:16-18"

Output:

    {
      "schema_version": "1.0",
      "book": "John",
      "chapter_start": 3,
      "verse_start": 16,
      "chapter_end": 3,
      "verse_end": 18,
      "original_text": "Jn 3:16-18"
    }


The six canonical cases, including `John 3:16-4:3`, are specified in
[SPECIFICATION.md, Section 6](SPECIFICATION.md#canonical-examples).
Schema version `"1.0"` is retained because this endpoint model corrects
the unpublished P0 draft.

## Guiding Principle

Normalize structure without inventing meaning.
