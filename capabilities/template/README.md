# CAIF Capability

A **CAIF Capability** is a reusable, governed unit of functionality that can
be used by human users, AI agents, applications, and other capabilities.

Capabilities are the primary building blocks of the CAIF Shared Core.

CAIF intentionally separates engineering infrastructure from domain
knowledge. A capability therefore defines stable behavior and semantic
contracts without depending unnecessarily on a particular application,
model provider, agent framework, database, or orchestration technology.

## Purpose

A CAIF Capability should:

- provide one clearly defined reusable function;
- expose stable inputs and outputs;
- use canonical CAIF contracts where applicable;
- support use by both humans and AI agents;
- declare governance and review requirements;
- remain independent of a particular AI runtime;
- be testable and evaluable independently;
- allow multiple implementations and adapters.

## Capability Structure

A mature capability may contain:

    <capability-name>/
    ├── README.md
    ├── SPECIFICATION.md
    ├── AGENTS.md
    ├── SKILL.md
    ├── contracts/
    ├── implementation/
    ├── adapters/
    ├── tests/
    ├── evaluation/
    ├── governance/
    ├── examples/
    └── CHANGELOG.md

Not every directory is required during initial development.

The four top-level Markdown files establish the minimum conceptual
definition of a capability before implementation begins.

## Core Documents

### README.md

Human-readable introduction.

It explains:

- what the capability does;
- why it exists;
- who uses it;
- typical use cases;
- dependencies;
- examples;
- implementation status.

### SPECIFICATION.md

Normative engineering specification.

It defines:

- required behavior;
- canonical inputs and outputs;
- semantic requirements;
- error conditions;
- governance requirements;
- interoperability requirements;
- acceptance criteria.

Implementations SHOULD conform to this specification.

### AGENTS.md

Development instructions for AI coding agents and human developers.

It defines:

- architectural boundaries;
- files that may be modified;
- required contracts;
- testing expectations;
- governance constraints;
- contribution rules.

### SKILL.md

Agent-readable operational description.

It explains to an AI agent:

- what capability is available;
- when it should be used;
- what inputs it expects;
- what outputs it returns;
- when it should not be used;
- when human review or escalation is required.

SKILL.md is an adapter-facing artifact. It does not replace
SPECIFICATION.md or canonical CAIF contracts.

## Capability-First Principle

Applications consume capabilities; capabilities do not belong to
applications.

For example:

    CKAIS ──────────────┐
                        │
    Sermon Ecosystem ───┼──> Retrieved Evidence Capability
                        │
    Biblical AI ────────┘

CKAIS may use one retrieval technology while another application uses a
different technology. If both conform to the same CAIF capability
specification and canonical contracts, they can interoperate without
sharing the same implementation.

## Technology Independence

A capability MAY be exposed through multiple adapters, including:

- Agent Skill
- Google ADK
- REST API
- A2A
- MCP
- command line interface
- future workflow or agent protocols

These mechanisms are replaceable.

The capability specification and semantic contracts are intended to
remain stable across changes in implementation technology.

## Governance

Capabilities involving doctrine, pastoral information, privacy,
security, institutional decisions, or other governed information MUST
declare their governance requirements.

A capability must not silently convert uncertain, disputed, unverified,
or externally supplied information into trusted knowledge.

## Status

This directory defines the initial CAIF capability model.

Specifications precede implementations.

The structure will evolve through implementation experience while
preserving backward-compatible contracts wherever practical.