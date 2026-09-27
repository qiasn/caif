# Google ADK Adapter Development

Read this adapter's README, the capability's README, SPECIFICATION.md and
SKILL.md, and the shared BiblePassageReference schema before changing this adapter.

- Translate framework invocation mechanics only. Capability semantics must not
  migrate into adapters: parsing, aliases, profiles, ambiguity, and validation
  remain authoritative in the existing capability.
- Never duplicate Bible resources or modify canonical contracts for ADK.
- Return successful capability dictionaries unchanged. Expected tool errors are
  adapter-local transport responses, not a CAIF normalization-result contract.
- Preserve operational/programming exceptions. Do not expose exception details
  or internal paths in expected user-facing errors.
- Keep framework-specific signatures, declarations, dependency pins, and error
  translation here. ADK API changes must not silently change CAIF semantics.
- Keep the checkout loader isolated and independent of the working directory;
  replace it when proper capability packaging is approved.
- Exercise the real pinned FunctionTool offline. Test generated declarations,
  forwarding, identity-preserving success, errors, and working-directory changes.
- Run ordinary pytest in this directory, then the unchanged P0-B suite (96 tests),
  and git diff --check. Do not introduce live model calls or credentials in tests.
- P0-C2 permits one minimal agent and an ephemeral in-memory session service
  for the explicit experiment only. No application, memory architecture,
  manifests, mapping JSON, or new contracts.
- Keep live calls separate from pytest and require explicit local model/API-key
  configuration. Never print credentials. Scripted-model tests verify plumbing,
  not autonomous model behavior.
- Canonical data is the tool result; final natural-language answers are
  presentation. Capture user text, model arguments, tool results and final
  responses separately. Do not repair rewritten model arguments in the adapter.
