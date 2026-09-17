# CAIF Capability Specification

Status: Draft  
Specification Version: 0.1

## 1. Purpose

This document defines the normative requirements for a reusable CAIF
Capability.

The key words MUST, MUST NOT, REQUIRED, SHOULD, SHOULD NOT, and MAY
indicate requirement strength.

## 2. Capability Definition

A CAIF Capability is a versioned, independently testable unit of
functionality that exposes defined behavior through canonical semantic
contracts.

A capability MUST define:

1. purpose;
2. inputs;
3. outputs;
4. behavior;
5. failure conditions;
6. governance requirements;
7. evaluation criteria;
8. version.

A capability SHOULD be usable independently of any single application.

## 3. Capability Identity

Each capability MUST declare:

    capability_id
    name
    version
    status
    owner
    description

Recommended capability identifiers use lowercase hyphenated names.

Example:

    capability_id: retrieved-evidence
    version: 0.1.0

## 4. Inputs

Inputs MUST be explicitly defined.

Each input SHOULD specify:

    name
    type
    required
    semantic meaning
    validation requirements
    privacy classification
    provenance requirements

Application-specific assumptions MUST NOT be hidden inside an input.

## 5. Outputs

Outputs MUST use canonical CAIF contracts when an applicable contract
exists.

Each output SHOULD specify:

    type
    semantic meaning
    provenance
    confidence or uncertainty when applicable
    governance status when applicable
    citations or evidence when applicable

An implementation MUST NOT change the semantic meaning of a canonical
output contract.

## 6. Behavior

The capability MUST describe observable behavior independently of its
implementation.

The specification defines WHAT the capability does.

Implementation code defines HOW it is done.

For example, a retrieval capability may specify:

    Query
        ↓
    Retrieve Evidence
        ↓
    Normalize
        ↓
    Rank
        ↓
    RetrievedEvidence[]

The specification SHOULD NOT require ChromaDB, LightRAG, PostgreSQL,
or another implementation technology unless that technology is itself
part of the capability requirement.

## 7. Canonical Contracts

Capabilities SHOULD communicate using shared CAIF contracts.

Examples may include:

- DocumentRecord
- RetrievedEvidence
- Citation
- AIAnswer
- GovernanceDecision
- WorkflowRequest
- WorkflowResult

Canonical contracts belong to the CAIF Shared Core rather than to an
individual application.

## 8. Provenance

Information entering a capability SHOULD retain sufficient provenance
to identify its source.

Where appropriate, outputs SHOULD distinguish among:

- source content;
- retrieved evidence;
- generated interpretation;
- inference;
- externally supplied assertion;
- reviewed institutional knowledge.

Loss of provenance MUST NOT silently promote information to a higher
trust status.

## 9. Governance

Every capability MUST declare whether governance evaluation is:

    NONE
    OPTIONAL
    REQUIRED

A governed capability MUST specify:

- applicable policies;
- access restrictions;
- review requirements;
- escalation conditions;
- prohibited automatic actions.

Human governance remains authoritative where CAIF policy requires
human review.

## 10. Domain Knowledge

The engineering definition of a capability SHOULD remain independent
of domain-specific knowledge whenever practical.

Domain implementations MAY supply:

- ontologies;
- knowledge bases;
- authority profiles;
- reasoning policies;
- evaluation sets;
- governance overlays.

This permits multiple domain-specific systems to use common CAIF
engineering capabilities without requiring common domain beliefs,
knowledge, or policies.

## 11. Agent Interoperability

A capability MAY be invoked by:

- a human;
- an application;
- an AI agent;
- another capability;
- an orchestrated workflow.

Runtime technologies MUST NOT redefine the semantic meaning of the
capability.

Agent frameworks orchestrate capabilities; canonical CAIF contracts
define interoperability.

## 12. Adapters

Implementations MAY provide adapters for technologies such as:

    Agent Skill
    Google ADK
    REST
    A2A
    MCP
    CLI
    Workflow systems

Adapters MUST preserve canonical capability semantics.

## 13. Failure and Uncertainty

A capability MUST define expected failure conditions.

A capability MUST NOT fabricate successful results when required
evidence or inputs are unavailable.

Where applicable it SHOULD distinguish:

    SUCCESS
    PARTIAL
    NOT_FOUND
    INSUFFICIENT_EVIDENCE
    POLICY_RESTRICTED
    REVIEW_REQUIRED
    ERROR

## 14. Evaluation

Every production capability SHOULD have evaluation criteria.

Evaluation MAY include:

- functional correctness;
- contract conformance;
- retrieval quality;
- provenance completeness;
- citation correctness;
- policy compliance;
- uncertainty calibration;
- interoperability;
- regression tests.

Domain-specific capabilities MAY add domain-specific evaluation suites.

## 15. Security and Privacy

Capabilities MUST follow applicable CAIF security, privacy, and access
policies.

Sensitive information MUST NOT be exposed merely because another agent
can technically request it.

Authorization precedes disclosure.

## 16. Versioning

Capabilities SHOULD use semantic versioning.

Breaking changes to canonical inputs, outputs, or semantics require a
major version change.

Implementation changes that preserve the capability contract SHOULD
NOT require consumers to change.

## 17. Acceptance Criteria

Before a capability is admitted to the CAIF Shared Core, it SHOULD
provide:

- a clear purpose;
- README.md;
- SPECIFICATION.md;
- AGENTS.md;
- SKILL.md;
- defined inputs and outputs;
- applicable canonical contracts;
- tests;
- evaluation criteria;
- governance requirements;
- an identified maintainer or owner;
- version information.

Implementation code is not sufficient by itself to define a CAIF
Capability.

## 18. Design Principle

CAIF standardizes durable meaning and governed capability behavior,
not temporary implementation technology.