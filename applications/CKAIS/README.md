# First CKAIS vertical slice

This is an architectural integration experiment, not production-ready CKAIS.
One application agent consumes the existing CAIF normalization tool:

```text
applications/CKAIS/ckais_agent.py
    -> adapters/google-adk/bible_reference_tool.py
    -> capabilities/bible-reference-normalization/bible_reference_normalization.py
    -> shared/contracts/BiblePassageReference.schema.json + capability resources
```

CKAIS owns request orchestration, a short application instruction, observation of
canonical results/errors, and optional presentation. CAIF owns parsing, aliases,
canon rules, chapter/verse validation, ambiguity, and canonical output semantics.
No lower layer imports CKAIS. No capability data or implementation is copied.

The existing checkout directories are not installable Python packages. An
isolated checkout-relative import bridge loads the existing adapter once,
independent of working directory. It can be removed when packaging is approved;
this slice makes no packaging changes to the lower layers.

`create_agent(model)` constructs one ADK Agent with the existing
`bible_reference_tool`. `observe_requests(model, messages)` uses the P0-C2
Agent/Runner/InMemorySessionService pattern, with a fresh session per request
and a five-model-call limit. This ephemeral execution session is not a shared
memory architecture. Successful tool payloads are retained unchanged in
`canonical_results`; adapter errors are retained in `tool_errors`. Both retain
call IDs for association with the separately recorded model `tool_calls`.
These observation records are application-local, not a new canonical contract.
Operational exceptions propagate; no partial success is fabricated.

**Canonical data is the CAIF tool result. Final prose is presentation.**
`presentation` can neither populate nor overwrite `canonical_results`.
No tool invocation means no canonical result. A later tool success remains a
separate observation rather than erasing a prior error. No final prose is parsed
back into a BiblePassageReference. The P0-C2 Genesis observation illustrates why:
null verse endpoints selecting whole chapters remained canonical even when the
LLM described explicit verse endpoints. Exact text preservation begins with the
model's supplied tool argument; it is not guaranteed from the original user span.

## Offline verification

From the repository root with Python 3.12:

```bash
source .venv/bin/activate
python -m pip install -r applications/CKAIS/requirements.txt
cd applications/CKAIS
pytest -v
```

Dependencies reference the existing pinned ADK 2.9.2 environment. No new
libraries are required. Tests use a scripted BaseLlm with the real ADK runner,
adapter and capability. They cover the normalization and intent-selection inputs, unchanged
payloads and original_text, and separation of data from presentation. The
scripted failure response deliberately claims success to verify that even
misleading model prose cannot manufacture an application canonical result.
This stress test does not predict real model behavior. Tests need no key or
network. Existing P0-C and P0-B tests remain separate and unchanged.

## Explicit live experiment

In your terminal configure `GOOGLE_GENAI_USE_VERTEXAI=FALSE`, `CAIF_ADK_MODEL`
with a model available to your account, and securely export `GEMINI_API_KEY` or
`GOOGLE_API_KEY`. The installed client prioritizes GOOGLE_API_KEY if both exist.
No secrets or model names are hard-coded, and no `.env` file is loaded/created.
From this directory with the repository virtual environment activated:

```bash
python - <<'PY'
import asyncio
import json
from ckais_agent import run_live_experiment

print(json.dumps(asyncio.run(run_live_experiment()), ensure_ascii=False, indent=2))
PY
```

This explicitly makes model/API calls for the configured examples; import and pytest
do not. It reports exact user input, generated tool arguments, canonical payloads
or errors, and final presentation separately. Inspect text preservation and
post-error behavior empirically; do not assume deterministic model behavior.
Live execution was not performed during initial implementation because model
configuration and API keys were absent from the process environment.


## Intent/capability-selection experiment

The application instruction first asks whether normalization can fulfill the
request. Explicit normalization/identification tasks may use the tool. Passage
text (including “What passage is Jn 3:16?”), explanation/interpretation, sermons,
and other unavailable operations receive a brief capability-unavailable response;
normalization must not substitute for fulfillment. Genuinely ambiguous requests
receive clarification before tool use. This is an application prompt policy,
not a router, registry, intent contract, or new CAIF semantic rule.

The live examples include explicit normalization, unavailable tasks, and an
ambiguous help request. Deterministic tests script those decisions and verify
that no-tool answers leave canonical results empty, while unsupported
normalization still retains the adapter error. They do not prove that a live
model will choose the correct intent. The revised instruction requires a new
live observation; no live call was made for this change.

## P1-B: controlled Joshua document retrieval

`joshua_document_experiment.py` is a separate experiment; P1-A remains unchanged.
CKAIS configures the three ignored PDFs and the experimental labels
`known_source`, `unverified`, `internal`. These are P1-B defaults, not permanent
church governance policy or access enforcement. Local filesystem paths never
appear in Citation.uri, which is null.

Dependencies flow from this application to the new ADK document tool, then the
framework-independent document-retrieval capability and unchanged evidence and
citation contracts. PDF pages and lexical term overlap are the initial profile,
not permanent limits of the generic capability. One original PDF page is one
full-text evidence unit; no OCR, summaries, chunk splitting or model ingestion.
The in-memory index is rebuilt locally; real source content is never written to
tracked files. The root ignore rule protects only `data/p1b-corpus/`.

### Requirements/design traceability

The application authorities are the SRS and SDD v2.2 under `docs/`.

| Authority | Exercised now | Simplified/deferred |
| --- | --- | --- |
| SRS 2.2, 2.3 | Search fellowship presentation records | Local files instead of upload/portal/authentication |
| SRS 3.1 | Parse PDF text | Other formats, tagging, inferred metadata deferred |
| SRS 3.2 and scenario 6 | Surface source evidence for questions | Lexical candidates and source excerpts instead of unrestricted generated answers |
| SRS 3.4 | Match existing English/Chinese text | No translation, script conversion or cross-language semantic search |
| SDD Capture/Normalize | Originals unchanged; machine-readable extraction | No OCR, enrichment, production storage or archival durability claims |
| SDD Provenance & Governance | Source hash and original page locator; explicit labels | No access-control workflow, audits or governance verification |
| SDD Retrieval & AI Reasoning; Source Preservation | Separate source evidence from generated prose | No vector search, feedback, adaptive memory or synthesized wisdom |
| SDD Relationship to P1-B | Controlled PDF ingestion/retrieval/citations | Immich/media, dictionary integration, databases and multi-agent work deferred |

### Output and limits

`load_corpus()` requires exactly three local PDFs. `corpus.retrieve(query)` returns
canonical evidence; `corpus.diagnostics` lists indexed, empty and visibility-
unsupported pages. `qualify_local_corpus()` returns these diagnostics without
source content. Empty pages preserve numbering but produce no evidence.

`observe_requests(model, messages, corpus=corpus)` follows P1-A's ADK Runner and
fresh-session pattern. It keeps tool arguments/responses, evidence, tool errors,
and `model_presentation` separate. The user-facing `presentation` identifies
candidate source pages or reports no matches/search failure. Evidence objects
supply the actual excerpts and citations; raw model prose is diagnostic only,
never treated as a Joshua answer. No matches cannot turn general model knowledge
into fellowship evidence. Keyword overlap does not prove a claim is supported;
this prototype returns source candidates, not a semantic-support guarantee.

Matching uses normalized copies, never edits content. Any overlapping query term
can match; ranking is deterministic. Contiguous Chinese runs match literally,
not through segmentation; long Chinese questions may miss results and common
words can produce irrelevant results. Missing matches do not prove absence from
the original documents, especially image-only or excluded pages.

### Tests and separate local qualification

Install `applications/CKAIS/requirements.txt` in the existing virtual environment.
Run ordinary `pytest -v` separately in `capabilities/document-retrieval`,
`adapters/google-adk`, and `applications/CKAIS`, plus the unchanged Bible suite.
Synthetic PDFs are created under pytest temporary directories. No real document
content, extracted index, or fixture is tracked. Real PDFs are not needed for tests.

From this directory, local qualification (no model or network):

```python
from joshua_document_experiment import qualify_local_corpus
print(qualify_local_corpus())
```

To inspect retrieval locally without a model:

```python
from joshua_document_experiment import load_corpus
corpus = load_corpus()
evidence = corpus.retrieve("search terms")
```

Keep private outputs local and out of Git. Optional model-driven presentation
requires explicit configuration/authorization and passes retrieved private pages
to that provider; it is not part of local corpus qualification. No live call is
performed on import or by tests. Review rendering/extraction fidelity separately:
pypdf's visibility screening is conservative, not a pixel-level visibility proof.
