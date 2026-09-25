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
- P0-C does not require agents, runners, manifests, mapping JSON, or new contracts.
