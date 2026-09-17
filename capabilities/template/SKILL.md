---
name: template
description: >
  Defines how an AI agent discovers, evaluates, and invokes a reusable
  CAIF capability while preserving canonical contracts, provenance,
  governance, and human review requirements.
version: 0.1.0
status: draft
---

# CAIF Capability Skill

## Purpose

Use this skill when a task can be satisfied by a reusable CAIF
capability.

A CAIF capability provides governed functionality through stable
semantic contracts independently of a particular application or agent
runtime.

## When to Use

Use a CAIF capability when:

- an existing capability matches the requested task;
- interoperability with another CAIF application is required;
- canonical CAIF inputs or outputs are available;
- provenance or governance must be preserved;
- the functionality should be reusable across applications.

Prefer an existing shared capability over creating duplicate
application-specific functionality.

## Invocation Procedure

Before invoking a capability:

1. identify the required capability;
2. verify that its declared purpose matches the task;
3. validate required inputs;
4. determine applicable access and governance requirements;
5. invoke an available implementation or adapter;
6. validate the returned canonical contract;
7. preserve provenance, citations, confidence, and review status;
8. return or pass the result to the requesting agent or application.

Conceptually:

    Intent
      ↓
    Capability Discovery
      ↓
    Input Validation
      ↓
    Governance Check
      ↓
    Capability Invocation
      ↓
    Contract Validation
      ↓
    Result + Evidence + Governance Status

## Do Not Use

Do not invoke a capability when:

- required inputs are unavailable;
- authorization is insufficient;
- the capability does not match the requested semantics;
- required governance conditions cannot be satisfied.

Do not substitute a superficially similar capability whose semantic
contract differs from the requested task.

## Outputs

Return outputs using the canonical contract defined by the capability
SPECIFICATION.md.

Do not silently remove:

- provenance;
- citations;
- uncertainty;
- trust status;
- review requirements;
- governance decisions.

## Uncertainty

If evidence is insufficient, report that condition explicitly.

Do not fabricate missing evidence.

When supported by the capability, use statuses such as:

    SUCCESS
    PARTIAL
    NOT_FOUND
    INSUFFICIENT_EVIDENCE
    POLICY_RESTRICTED
    REVIEW_REQUIRED
    ERROR

## Governance

If the capability declares governance evaluation as REQUIRED, the
governance step must not be skipped.

If human review is required, return REVIEW_REQUIRED and the information
needed by the reviewer.

The agent must not impersonate the required human authority.

## Interoperability

The same capability may be exposed through different technologies,
including Agent Skill, Google ADK, REST, A2A, MCP, CLI, or future
workflow systems.

Invocation technology does not change capability semantics.

## Guiding Principle

Discover by capability.

Invoke through an available adapter.

Communicate through canonical contracts.

Preserve provenance.

Obey governance.

Escalate when human authority is required.