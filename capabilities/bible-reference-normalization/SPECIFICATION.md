# Bible Reference Normalization Capability Specification

Status: Draft  
Specification Version: 0.1  
Capability ID: `bible-reference-normalization`

## 1. Purpose

This specification defines the normative behavior of the CAIF
Bible Reference Normalization capability.

The capability converts human-written English or Chinese Bible
references into a canonical structured representation suitable for
use by CAIF applications, agents, retrieval systems, and other
capabilities.

Examples include:

    John 3:16
    Jn 3:16-18
    John 3
    Jude 5
    Genesis 1-3
    約翰福音三章十六節
    約三16
    創世紀1-3章
    創1-3

The capability performs structural normalization only.

It does not interpret Scripture, determine doctrine, perform exegesis,
or evaluate the theological meaning of a passage.

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY indicate
requirement strength.

---

## 2. Capability Identity

The capability SHALL declare:

    capability_id: bible-reference-normalization
    name: Bible Reference Normalization
    version: 0.1.0
    status: draft

The capability is intended to be reusable by multiple CAIF
applications and MUST NOT depend on CKAIS, BiblicalAI, SermonAI,
or another individual application.

---

## 3. Supported Canon

Version 0.1 of this capability MUST support the 66 books of the
Protestant Bible canon.

The initial implementation is NOT REQUIRED to normalize
deuterocanonical or other books used by Catholic, Orthodox, or other
canonical traditions.

The design MUST NOT, however, make future support for other canon
profiles impossible.

Canon-specific information SHOULD therefore remain explicit where
needed rather than being embedded irreversibly in parsing logic.

Other organizations or downstream projects MAY extend or adapt the
open-source capability to support additional canon profiles.

---

## 4. Supported Languages

Version 0.1 MUST support Bible references written in:

- English
- Chinese

The capability SHOULD recognize commonly used English and Chinese
book names and abbreviations.

Examples that MUST be supported include:

    John 3:16
    Jn 3:16
    約翰福音3:16
    約三16

The normalized canonical book identity MUST NOT depend on the
language used in the original reference.

The original user-entered text MUST be preserved.

The architecture SHOULD permit additional languages to be added
without changing the canonical semantics of the output contract.

---

## 5. Inputs

The primary required input is:

    raw_reference: string

Example:

    "Jn 3:16-18"

Optional contextual inputs MAY include:

    language
    canon_profile
    surrounding_text

`language` MAY be supplied when already known.

If language is not supplied, an implementation MAY detect the
language from the input.

`canon_profile`, when omitted in Version 0.1, SHALL default to the
supported Protestant 66-book canon profile.

`surrounding_text` MAY be used to assist recognition or ambiguity
detection but MUST NOT be used to invent a Biblical reference that
is not reasonably supported by the supplied text.

---

## 6. Outputs

A successful normalization MUST return a canonical
`BiblePassageReference` object.

The output MUST conform to the applicable CAIF contract located at:

    shared/contracts/BiblePassageReference.schema.json

The canonical representation MUST be capable of expressing:

- a whole chapter;
- a single verse;
- a verse range;
- a chapter range;
- the original textual reference;
- language when known;
- canon profile when applicable;
- normalization confidence or ambiguity status when applicable.

Example input:

    Jn 3:16-18

Conceptual normalized result:

    {
      "book": "John",
      "chapter_start": 3,
      "chapter_end": 3,
      "verse_start": 16,
      "verse_end": 18,
      "original_text": "Jn 3:16-18"
    }

The exact JSON representation MUST follow the current canonical
`BiblePassageReference` schema.

---

## 7. Normalization Behavior

The capability MUST:

1. identify the Biblical book;
2. normalize recognized book names and abbreviations to a canonical
   book identity;
3. identify chapter information;
4. identify verse information when present;
5. recognize verse ranges;
6. recognize chapter ranges;
7. preserve the original reference text;
8. distinguish valid abbreviated forms from ambiguous references;
9. report ambiguity rather than silently guessing;
10. produce output conforming to the canonical CAIF contract.

Normalization MUST preserve the meaning of the reference rather than
merely rewriting its textual appearance.

---

## 8. Whole-Chapter References

A book followed by a chapter number without a verse number SHALL
represent the entire chapter for books having more than one chapter.

Example:

    John 3

means:

    the entire third chapter of the Gospel of John

It MUST NOT be silently interpreted as John 3:1 or another individual
verse.

---

## 9. Single-Chapter Books

For a Biblical book containing only one chapter, a single number
following the book name SHALL normally be interpreted as a verse
number.

Example:

    Jude 5

SHALL normalize to the equivalent of:

    Jude 1:5

The normalized representation MUST preserve the canonical chapter
number:

    chapter = 1
    verse = 5

The same rule SHOULD apply consistently to other supported
single-chapter Biblical books.

An implementation MUST NOT interpret `Jude 5` as chapter 5 because
no such chapter exists.

---

## 10. Chapter Ranges

The capability MUST support references spanning complete chapters.

Examples:

    Genesis 1-3
    創世紀1-3章
    創1-3

These references SHALL represent Genesis chapters 1 through 3,
inclusive.

A chapter range MUST be distinguishable in the canonical contract
from a verse range.

The implementation MUST NOT reinterpret:

    Genesis 1-3

as:

    Genesis 1:3

when the syntax and context indicate a chapter range.

---

## 11. Verse Ranges

The capability MUST support references spanning multiple verses
within a chapter.

Example:

    John 3:16-18

SHALL represent:

    John 3:16 through John 3:18

The normalized output MUST identify the beginning and ending verses
without losing the chapter identity.

---

## 12. Chinese Reference Normalization

The capability MUST support commonly used Chinese Bible book names
and abbreviations.

For Version 0.1, examples that MUST normalize correctly include:

    約翰福音3:16
    約三16
    創世紀1-3章
    創1-3

For example:

    約三16

SHALL be semantically equivalent to:

    John 3:16

and:

    創1-3

SHALL be semantically equivalent to:

    Genesis 1-3

Chinese input MUST NOT require translation by the user before
normalization.

Chinese and English forms referring to the same passage MUST produce
the same canonical passage identity while preserving their respective
original text.

---

## 13. Original Text Preservation

The capability MUST preserve the original user-supplied reference.

Example:

Input:

    約三16

The canonical object SHOULD contain:

    original_text: "約三16"

even though the canonical book identity is normalized to `John`.

Normalization MUST NOT destroy the original representation.

This requirement supports provenance, debugging, user clarification,
and future improvements to normalization.

---

## 14. Ambiguity

The capability MUST NOT silently guess when more than one reasonable
normalization exists.

An ambiguous result MUST be explicitly identified.

During development and testing, ambiguous references SHOULD be
presented to the human tester for clarification.

The tester's response SHOULD be used to:

1. determine the intended interpretation;
2. determine whether the ambiguity represents a missing normalization
   rule;
3. add or modify the rule when appropriate; and
4. add a regression test so that the resolved case remains correct.

The implementation MUST NOT merely memorize a tester's answer when
the underlying ambiguity requires a general normalization rule.

In deployed applications, unresolved ambiguity SHALL result in a
clarification request to the user.

Example interaction:

    User:
    [ambiguous reference]

    System:
    "I am not certain which Bible passage you mean.
     Did you mean ...?"

The capability MUST NOT invent an interpretation solely to avoid
asking for clarification.

---

## 15. Invalid and Unsupported References

The capability MUST detect references that cannot be validly
normalized.

Examples include:

- unknown book names;
- nonexistent chapters;
- nonexistent verses;
- malformed ranges;
- unsupported canonical books;
- input that does not contain sufficient information to identify a
  passage.

The capability MUST NOT fabricate a valid Bible reference from
invalid input.

The result SHOULD distinguish among conditions such as:

    SUCCESS
    AMBIGUOUS
    INVALID_REFERENCE
    UNSUPPORTED_CANON
    INSUFFICIENT_INFORMATION
    ERROR

The exact result representation MAY be refined as the implementation
and canonical contracts mature.

---

## 16. Boundary of Responsibility

This capability performs Bible reference normalization only.

It MUST NOT:

- interpret the meaning of Scripture;
- determine whether an interpretation is doctrinally correct;
- perform exegesis;
- generate sermons;
- resolve theological disagreements;
- select verses to support a theological claim;
- promote one interpretation of a passage over another.

For example:

    Romans 3:28

may be normalized structurally.

Questions about the theological meaning of Romans 3:28 belong to
other CAIF or BiblicalAI capabilities.

This separation MUST be preserved even if an LLM is used internally
by an implementation.

---

## 17. Technology Independence

The specification defines required behavior, not implementation
technology.

An implementation MAY use:

- deterministic parsing;
- regular expressions;
- lookup tables;
- Unicode normalization;
- language-specific parsing;
- an LLM;
- combinations of these techniques;
- future technologies.

No particular implementation technique is required as long as the
observable behavior conforms to this specification.

Google ADK, Agent Skills, A2A, MCP, REST, CLI, and other invocation
technologies MUST NOT redefine the semantic meaning of this
capability.

---

## 18. Provenance

The original reference text MUST be preserved.

When available, the implementation SHOULD also preserve relevant
context such as:

- input language;
- canon profile;
- normalization confidence;
- source or calling application when supplied.

Normalization metadata MUST NOT be confused with the Biblical text
itself.

---

## 19. Governance

This capability performs structural normalization and normally does
not require theological review.

Governance classification for Version 0.1 is:

    OPTIONAL

The capability MUST NOT make theological or doctrinal judgments under
the guise of reference normalization.

Changes to the supported canon profile SHOULD receive human review
because such changes alter the defined domain boundary of the
capability.

---

## 20. Security and Privacy

The capability SHOULD require only the information necessary to
normalize the supplied reference.

It MUST NOT require access to unrelated pastoral, personal, church,
or application data.

If surrounding text is supplied for disambiguation, that text MUST
remain subject to applicable CAIF privacy and access policies.

---

## 21. Evaluation

The implementation MUST be tested against representative English and
Chinese references.

The initial evaluation suite MUST include at least the following
semantic cases:

    John 3
        → entire chapter John 3

    John 3:16
        → John 3:16

    Jn 3:16-18
        → John 3:16-18

    約三16
        → John 3:16

    Jude 5
        → Jude 1:5

    Jude 1:5
        → Jude 1:5

    Genesis 1-3
        → Genesis chapters 1 through 3

    創世紀1-3章
        → Genesis chapters 1 through 3

    創1-3
        → Genesis chapters 1 through 3

The evaluation suite MUST also include:

- invalid book names;
- nonexistent chapters;
- nonexistent verses;
- malformed ranges;
- ambiguous inputs;
- unsupported canonical books.

Every corrected normalization defect SHOULD result in a regression
test.

---

## 22. Acceptance Criteria

Version 0.1 of the capability is acceptable for initial CAIF use when:

1. all 66 Protestant canonical books can be represented;
2. supported English book names and abbreviations normalize correctly;
3. supported Chinese book names and abbreviations normalize correctly;
4. whole-chapter references are distinguished from verse references;
5. single-chapter books are handled correctly;
6. chapter ranges are distinguished from verse ranges;
7. original reference text is preserved;
8. ambiguous references are not silently guessed;
9. invalid references are not fabricated into valid references;
10. outputs conform to the canonical
    `BiblePassageReference` contract;
11. required tests pass;
12. theological interpretation remains outside the capability.

---

## 23. Versioning

This capability SHOULD use semantic versioning.

Version 0.1 is intentionally limited to English and Chinese
normalization of the Protestant 66-book canon.

Future versions MAY add:

- additional abbreviations;
- additional languages;
- improved ambiguity handling;
- additional syntactic forms;
- optional additional canon profiles.

Such extensions MUST preserve backward compatibility whenever
practical.

A breaking change to canonical semantics requires an appropriate
major-version change.

---

## 24. Design Principle

Normalize the reference, preserve the source, expose uncertainty,
and do not invent meaning.