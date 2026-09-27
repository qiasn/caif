# CAIF Google ADK Adapter

This P0-C adapter connects Google ADK invocation mechanics to the existing
[bible-reference-normalization capability](../../capabilities/bible-reference-normalization/README.md).
It does not parse references, duplicate resources, or redefine CAIF semantics.
The capability's [specification](../../capabilities/bible-reference-normalization/SPECIFICATION.md),
[skill](../../capabilities/bible-reference-normalization/SKILL.md), implementation,
and [BiblePassageReference contract](../../shared/contracts/BiblePassageReference.schema.json)
remain authoritative and unchanged.

## Environment and installation

Tested with **google-adk 2.9.2**, Python 3.12, and pytest 9.1.1. Python 3.12
preserves the capability's Unicode 15.0.0 requirement. From the repository root:

```bash
source .venv/bin/activate
python -m pip install -r adapters/google-adk/requirements.txt
cd adapters/google-adk
pytest -v
```

Requirements reference the existing capability dependencies and pin the tested
ADK environment's resolved packages. No ADK extras are required. This is a
checkout-based adapter, not a separately distributable package. Its isolated
loader resolves the original capability file relative to this adapter, preserves
its source location, and caches the loaded module. Neither resource lookup nor
runtime invocation depends on the process working directory. Replace the loader
when CAIF adopts Python packaging; do not copy the capability to package it here.

## Tool registration and invocation

`bible_reference_tool.py` exports the typed synchronous wrapper
`normalize_bible_reference(raw_reference, language=None, canon_profile=None)`
and the actual ADK `FunctionTool` instance `bible_reference_tool`. A consuming
application registers that instance in its ADK agent's `tools` list. The separate
P0-C2 experiment below supplies one minimal agent and runner, not a deployment
application.

From this adapter directory, an offline Python invocation is:

```python
import asyncio
from bible_reference_tool import bible_reference_tool

reference = asyncio.run(bible_reference_tool.run_async(
    args={"raw_reference": "約三16"},
    tool_context=None,
))
```

`None` works for this context-free tool's offline invocation; a hosting ADK runtime
normally supplies ToolContext. The tool does not request confirmation or access
session state. No model call, API credential, or network access is needed for
these tests. The tests use the installed ADK, not a mocked FunctionTool.

The tool declaration exposes exactly one required string, `raw_reference`, and
two optional nullable strings, `language` and `canon_profile`, defaulting to
`None`. Arguments are passed unchanged; defaults and interpretation belong to
the capability. Success returns the exact dictionary supplied by the capability,
which already validates it against the canonical schema. No success envelope,
status, confidence, or ADK metadata is added.

Preservation of `original_text` begins at the supplied tool argument. A host
requiring exact preservation of upstream text must forward that text unchanged,
rather than ask an LLM to rewrite it. Consumers must use the canonical tool
payload, not treat a later model paraphrase as the canonical reference.

## Adapter-local errors

`AmbiguousReference`, `UnsupportedSyntax`, and `InvalidReference` become:

```json
{
  "error": {
    "type": "AmbiguousReference",
    "message": "The reference is ambiguous. Ask the caller to clarify."
  }
}
```

Messages are fixed and safe; raw exception details and internal paths are not
forwarded. Other expected error types tell the caller to supply supported syntax
or check the reference/options. The adapter never guesses a correction.
This is an ADK-facing transport response, **not** a CAIF result contract or a
BiblePassageReference. No partial canonical object is returned on failure.
`ResourceConfigurationError` and all unexpected exceptions propagate to the host
as operational/programming failures.

## Version-sensitive ADK behavior

In the installed 2.9.2 release, declaration generation uses
`parameters_json_schema` and emits an experimental-feature warning. The schema
represents nullable strings using `anyOf` and requires only `raw_reference`.
Tests inspect `_get_declaration()`, an ADK private API, because it exposes the
actual generated declaration; review that test when upgrading ADK.

ADK itself returns an `error` string when a required argument is missing, before
calling the wrapper. It also filters undeclared arguments before invocation.
That framework error differs from this adapter's expected-reference errors;
neither is a CAIF contract. Tests pin these observed behaviors. Type annotations
supply a model-facing declaration, not a replacement for capability validation.

## Regression verification

After the adapter suite, run the untouched P0-B suite:

```bash
cd ../../capabilities/bible-reference-normalization
pytest -v
```

It must still report 96 passing tests. Adapter tests also compare results with
independent direct calls, validate success against the existing contract, verify
argument forwarding and exact object preservation, exercise exception handling,
and load/invoke the adapter from an unrelated working directory.


## P0-C2: explicitly invoked agent experiment

`minimal_agent.py` constructs one `Agent` with only `bible_reference_tool`.
Its short instruction asks for normalization through the tool and clarification
on errors, without teaching Bible-reference semantics. `Runner.run_async` uses
`InMemorySessionService.create_session` with a fresh session per example so
examples do not influence each other. This service supplies ADK's required
execution session, not a memory architecture. Each interaction is limited to
five model calls.

**Canonical data = tool result. Natural-language final answer = presentation,
not canonical data.** Final prose is never parsed back into a CAIF object.

The experiment returns observation records containing:

- `user`: the exact request and a separately recorded expected reference span;
- `tool_calls`: actual model function-call IDs, names and arguments;
- `adapter_returns`: copies observed by an after-tool callback that returns None;
- `tool_responses`: ADK function-response event payloads, including errors;
- `final_responses`: final non-thought text, kept separate from canonical data;
- `events`: the complete yielded ADK events;
- `checks`: event/adapter equality and exact reference-text comparisons, with
  null for inapplicable checks. Empty calls/results remain empty if no tool runs.

These are experiment observations, not a CAIF result contract. Multiple calls,
rewritten arguments, retries and missing final responses are retained, not
silently corrected. An error result is not labeled a canonical passage.
The four requested references plus `Please normalize John 3:16,18` are included.
The expected reference spans are used only for comparison, never fed into the
agent to choose its arguments.

### Manual configuration and live invocation

This minimal experiment deliberately uses Gemini Developer API. It checks for
`CAIF_ADK_MODEL` and `GOOGLE_API_KEY` or `GEMINI_API_KEY`, and rejects Vertex AI
mode. ADK's installed GenAI client prioritizes GOOGLE_API_KEY when both keys are
set. Choose a Gemini model ID currently available to your account with function
calling support. No default model or credential is embedded in source.

In your local terminal, activate the repository virtual environment and set
`GOOGLE_GENAI_USE_VERTEXAI=FALSE` and `CAIF_ADK_MODEL` to that model ID. Export a
key locally through your normal secret-management method (or a hidden terminal
prompt). Do not put it in source, shell history, captured experiment output, or
chat. The program does not automatically load `.env` files. No Vertex project,
location, or ADC credentials are needed for this chosen route.

From `adapters/google-adk`, invoke explicitly in Python, outside pytest:

```python
import asyncio
import json
from minimal_agent import run_live_experiment

observations = asyncio.run(run_live_experiment())
print(json.dumps(observations, ensure_ascii=False, indent=2))
```

This makes real model/API calls and may incur charges. It is not run on import
or by ordinary pytest. Preserve the printed observations for inspection; the
experiment does not automatically write files. Instructions request exact text,
but do not guarantee model tool selection, arguments, or final wording.

### Verification status

The user-run live P0-C2 experiment completed successfully with
`gemini-3.5-flash-lite` and ADK 2.9.2. The following empirical results were
reported by the user for this run:

- All five model-generated tool calls preserved the designated reference span
  exactly: `約三16`, `Jn 3:16`, `創世紀1-3章`, `Jude 5`, and `John 3:16,18`.
- All four successful canonical results preserved `original_text`. ADK event
  tool-response payloads equaled the corresponding adapter returns.
- `John 3:16,18` reached the tool unchanged, was rejected as
  `UnsupportedSyntax`, and was not converted by the agent into a successful
  canonical result.
- `Jude 5` was passed unchanged and normalized by CAIF to Jude 1:5,
  demonstrating that single-chapter semantics remained in the capability,
  not the agent.
- For Genesis, the canonical result selected whole chapters 1–3 with null
  verse endpoints. The final LLM prose presented this as `1:1-3:24`.
  This elaboration was presentation, not a change to the canonical tool result.
  Final prose MUST NOT replace the canonical tool result or be parsed back
  into it.

These observations establish the behavior of this model in this run, not a
guarantee for other models or future runs. Exact reference-text preservation
and post-error agent behavior remain model-sensitive. No full transcripts,
thought signatures, credentials, or invocation identifiers are recorded here.

Offline tests use a scripted `BaseLlm` with the real Agent, Runner, FunctionTool,
and unchanged capability. They verify the event capture and expected error flow;
they do not demonstrate autonomous model judgment or exact-text preservation by
a live LLM. Run ordinary `pytest -v` here: 24 original P0-C1 tests plus the P0-C2
tests. P0-B remains a separate, unchanged 96-test suite. No new dependencies are
required. Installed ADK emits its declaration experimental warning and an
upstream BaseAgentConfig deprecation warning during these tests.
