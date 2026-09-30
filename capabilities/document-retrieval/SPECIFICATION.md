# Document Retrieval Specification

Status: P1-B prototype; capability version 0.1.0.

## Generic semantics

Retrieve source-grounded evidence from a caller-controlled document corpus.
The capability owns extraction, source identity, evidence selection, provenance,
and validation. It MUST NOT depend on CKAIS, Joshua, ADK, or a model provider.
Successful results are lists of existing CAIF RetrievedEvidence objects with
canonical Citation objects. Evidence MUST retain source content and a locator;
generated answers, summaries, and inferred facts MUST NOT become source evidence.
No matches returns an empty list, not a fabricated answer. Operational extraction
or configuration failures MUST be distinguishable from no matches.

Corpus configuration supplies provenance, trust and access labels. These labels
are assertions of the caller, not an access-control mechanism or a verification
of truth. Never promote trust as a consequence of a lexical match.

## Initial P1-B implementation profile

PDF, pypdf, full-page evidence, and lexical ranking are implementation choices,
not permanent restrictions on the generic capability above.

- Load explicitly selected local PDFs into memory, preserving original bytes.
- One original physical PDF page is one evidence unit, numbered from 1. Never
  split, merge, summarize, OCR, paraphrase, translate, or expand page text.
- Preserve the extractor's page string in content. Matching uses a separate copy.
- Empty pages produce diagnostics and no evidence; later pages keep original
  numbering. Pages with detected unsupported visibility constructs are excluded
  in full and diagnosed; do not emit partially filtered pages.
- Inspect text-painting state for invisible/clipping text modes, opacity/masks,
  optional content, cropped pages, and nested forms. Axis-aligned full-page
  clipping is allowed with 0.001 PDF-point tolerance for exporter rounding;
  other clipping active during text painting excludes the page. This conservative screening
  does not establish pixel-level visibility or correct reading order in arbitrary
  PDFs. Controlled-corpus human qualification remains necessary, particularly
  for text covered by images or shapes. Never claim hidden/OCR-layer content is
  verified visible merely because pypdf extracted it.
- Derive source_id from SHA-256 of source bytes, evidence_id from source_id and
  physical page. Deduplicate identical PDFs. Modified bytes create a new identity.
- Citation uses source_type=document, location='PDF page N', filename as title,
  and uri=null. Do not expose absolute filesystem paths in canonical metadata.
- Validate every evidence object against the unchanged RetrievedEvidence schema,
  resolving Citation locally without network access.
- P1-B ranking: NFC/casefold and collapse whitespace in a search-only copy;
  unique ASCII alphanumeric runs and contiguous Han runs are query terms.
  Match Han terms as substrings and ASCII terms at ASCII alphanumeric boundaries;
  accept any overlap, rank by number of matched terms, then total
  occurrences, then source_id and page. Return bounded top_k (1..20).
  This is deterministic term overlap, not a probability or proof of support.
  Chinese runs are literal terms, not word segmentation; no script conversion,
  synonyms, cross-language search or semantic inference. Common words and short
  terms can produce false positives; long Chinese questions can miss matches.
- Invalid/empty queries and invalid limits raise ValueError. I/O, corrupt PDF,
  encrypted PDF, and contract failures raise DocumentRetrievalError.

## Acceptance

Use synthetic PDFs for reproducible tests: exact pages, original numbering,
blank/unsupported pages, source IDs, deterministic overlaps and ties, Chinese
text, no matches, operational failures, canonical conformance and caller labels.
Qualify private PDFs separately, reporting counts/locators only. Never copy their
content into source, fixtures, generated indexes or committed output.
