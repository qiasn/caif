# Document Retrieval

Framework-independent retrieval of source-grounded evidence from a controlled
corpus. See SPECIFICATION.md for durable semantics and the initial P1-B profile.

`PdfCorpus(paths, provenance_status=..., trust_status=...,
access_classification=...)` loads selected PDFs into memory. `retrieve(query,
top_k=5)` returns validated RetrievedEvidence dictionaries with Citation objects.
`diagnostics` reports each source/page as indexed, empty, or visibility-unsupported.
No on-disk index, OCR, LLM, network service, or database is used.

pypdf 6.19.0 (BSD-3-Clause) performs extraction. Text extraction is not rendering:
font mappings, reading order and occlusion require controlled-corpus review.
Conservative screening rejects detected unsupported visibility constructs rather
than silently emitting partial source pages. Sources and extracted text are not
logged or persisted. Returned citation URI is null.

From this directory with the repository Python 3.12 virtual environment active:
`pip install -r requirements.txt`, then `pytest -v`.
