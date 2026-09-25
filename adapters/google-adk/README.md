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
application registers that instance in its ADK agent's `tools` list. No agent,
runner, model configuration, or deployment application is supplied here.

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
