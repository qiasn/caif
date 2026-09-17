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
    preferred_canon
    surrounding_text

## Outputs

Return:

    BiblePassageReference

The output MUST conform to the canonical schema located at:

    shared/contracts/BiblePassageReference.schema.json

## Behavior

The capability should:

1. recognize common Biblical book names and abbreviations;
2. normalize book identity;
3. extract chapter numbers;
4. extract verse or verse ranges when present;
5. preserve the original reference text;
6. indicate ambiguity rather than guessing when interpretation is uncertain.

## Do Not Use

Do not use this capability to:

- interpret the theological meaning of a passage;
- determine doctrine;
- generate exegesis;
- decide whether a Biblical interpretation is correct.

This capability normalizes references only.


## Uncertainty

If more than one interpretation is plausible, return an ambiguous or
review-required result rather than silently selecting one.

Example:

    "John 3"

may mean the whole chapter and is valid.

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
      "book": "John",
      "chapter": 3,
      "verse_start": 16,
      "verse_end": 18,
      "original_text": "Jn 3:16-18"
    }


## Guiding Principle

Normalize structure without inventing meaning.