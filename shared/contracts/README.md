# CAIF Canonical Contracts

CAIF Canonical Contracts define stable semantic objects exchanged
between CAIF applications, capabilities, agents, and services.

They provide a common language across independently developed
implementations.

A canonical contract defines WHAT an exchanged object means.

It does not define:

- which database produced it;
- which LLM produced it;
- which agent framework invoked it;
- which programming language implemented it;
- which transport protocol carried it.

## Purpose

Canonical contracts enable CAIF applications and capabilities to
interoperate without requiring identical implementations.

For example:

    CKAIS
       │
       │ retrieves
       ▼
    RetrievedEvidence
       │
       │ consumed by
       ▼
    BiblicalAI

CKAIS may use ChromaDB while another system uses LightRAG,
PostgreSQL, GraphRAG, or a future retrieval technology.

If both produce conforming RetrievedEvidence objects, downstream
systems can process them consistently.

## Relationship to Capabilities

Capabilities define reusable behavior.

Contracts define reusable meaning.

Example:

    capability:
        sermon-retrieval

    input:
        SearchQuery

    output:
        RetrievedEvidence[]

The capability specification determines how retrieval behaves.

RetrievedEvidence.schema.json determines the semantic structure of
each returned evidence object.

## Relationship to Agent Skills

SKILL.md tells an AI agent:

- when to invoke a capability;
- what inputs it requires;
- what outputs to expect;
- what constraints apply.

Canonical contracts tell agents and applications what those inputs
and outputs mean.

Agent frameworks and skill formats may change over time.

Canonical semantic contracts should remain stable wherever possible.

## Contract Principles

CAIF contracts SHOULD:

1. use explicit field names;
2. preserve provenance;
3. distinguish source content from generated interpretation;
4. expose uncertainty where applicable;
5. expose governance status where applicable;
6. avoid implementation-specific fields in canonical semantics;
7. support versioning;
8. be independently validated.

## JSON Schema

Contracts are initially expressed using JSON Schema.

An implementation MAY internally use:

- Python models;
- Pydantic;
- TypeScript interfaces;
- Java classes;
- Protocol Buffers;
- database records;
- other representations.

However, exchanged canonical objects SHOULD conform to the applicable
CAIF contract.

## Versioning

Every canonical contract SHOULD contain a schema version.

Breaking semantic changes require a new major version.

Backward-compatible additions should normally use optional fields.

## Extension

Applications MAY add application-specific metadata, but they MUST NOT
silently redefine canonical fields.

Implementation-specific information should normally be placed under:

    extensions

Example:

    "extensions": {
      "ckais": {
        "collection": "sermons-2026"
      }
    }

Downstream consumers must be able to ignore extensions safely.

## Governance

A valid JSON object is not automatically trusted information.

Contracts may carry:

- provenance;
- confidence;
- review status;
- governance decisions;
- access classifications.

The contract preserves this information so downstream agents do not
silently increase the trust level of information.

## Initial Contracts

The initial CAIF Shared Core defines:

- BiblePassageReference
- Citation
- RetrievedEvidence
- GovernanceDecision
- ReviewDecision

Additional contracts should be added only when two or more
capabilities or applications need the same durable semantic concept.

## Design Principle

Standardize meaning before standardizing implementation.