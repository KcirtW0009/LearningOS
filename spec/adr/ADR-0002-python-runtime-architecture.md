---
id: ADR-0002
title: Python Runtime Architecture
status: Accepted
date: 2026-07-12
owner: Learning OS

related:
  - LOS-0400
  - LOS-0401
  - LOS-0406
---

# ADR-0002: Python Runtime Architecture

## Status

Accepted

---

# Context

Learning OS requires a first Runtime implementation to validate the core architecture.

The Runtime must support:

- Graph loading;
- Node interpretation;
- User State management;
- Local persistence;
- Command interaction.

Several implementation approaches are possible:

- simple scripting;
- Python package architecture;
- web application architecture;
- desktop application architecture.

The first implementation should minimize unnecessary complexity while preserving future extensibility.

---

# Decision

The first Learning OS Runtime implementation will use:

```
Python

+

Package-based Architecture

+

Local First Execution
```

---

# Python Selection

The Runtime prototype will be implemented in Python.

---

# Reasons

## Rapid Development

Python provides:

- simple syntax;
- large ecosystem;
- fast iteration.

This is suitable for validating system architecture.

---

## AI Development Compatibility

Python is widely supported by:

- AI coding agents;
- machine learning tools;
- developer ecosystems.

This improves future integration possibilities.

---

## Future AI Extension

Although the core Runtime does not depend on AI, Python provides compatibility with future optional extensions:

- machine learning tools;
- data processing;
- LLM interfaces.

---

# Package Architecture Decision

The Runtime will use a package-oriented structure.

Example:

```
runtime/

└── los/

    ├── graph/

    ├── state/

    ├── storage/

    ├── engine/

    └── cli/
```

---

# Reasons

## Separation of Responsibilities

Different Runtime components remain independent.

Example:

```
Graph

State

Storage

Interface
```

---

## Maintainability

A package structure prevents:

- oversized files;
- hidden dependencies;
- unclear ownership.

---

## Extension Capability

Future components can be added:

```
runtime/

├── ai/

├── plugins/

└── visualization/
```

without modifying existing core modules.

---

# Rejected Alternatives

## Single Script Architecture

Example:

```
main.py

graph.py

state.py
```

Rejected because:

- difficult to scale;
- encourages tight coupling;
- requires later migration.

---

## Web Application First

Rejected because:

- introduces frontend/backend complexity;
- requires deployment infrastructure;
- does not validate Runtime Core.

---

## Desktop Application First

Rejected because:

- UI complexity may hide architecture problems;
- prototype goal is Runtime validation.

---

# Local First Decision

The first Runtime will operate locally.

Requirements:

- no mandatory cloud service;
- no user account;
- no online dependency.

---

# Reasons

## User Data Ownership

Learning progress belongs to the user.

---

## Simplicity

Local execution reduces:

- deployment complexity;
- security concerns;
- maintenance cost.

---

# Core Architecture Boundary

The implementation MUST follow:

```
Interface

    ↓

Runtime Core

    ↓

Graph / State / Storage
```

---

# Runtime Core Principle

The Runtime Core MUST NOT depend on:

- CLI implementation;
- UI framework;
- external AI service.

---

# Dependency Policy

New dependencies SHOULD:

- solve clear problems;
- reduce complexity;
- be actively maintained.

Dependencies SHOULD NOT be added only for convenience.

---

# Performance Decision

The first Runtime prioritizes:

```
Correctness

>

Maintainability

>

Performance
```

---

# Consequences

## Positive Consequences

- Fast prototype development;
- Clear architecture;
- Easy AI-assisted development;
- Future extension compatibility.

---

## Negative Consequences

- Not optimized for large-scale deployment;
- Limited initial user interface;
- Python runtime overhead.

These limitations are acceptable for prototype stage.

---

# Future Evolution

Future versions MAY introduce:

- desktop applications;
- web interfaces;
- cloud synchronization;
- alternative runtime implementations.

However:

Future implementations SHOULD preserve:

- Graph model;
- State model;
- Storage abstraction.

---

# Architecture Principle

The first Runtime is not the final product.

It is the validation platform for Learning OS architecture.

---

# Acceptance Criteria

This ADR is complete when:

- implementation language is defined;
- package architecture is defined;
- runtime boundaries are protected;
- future evolution remains possible.

---

# Agent Note

When implementing Runtime:

1. Use Python.
2. Use package architecture.
3. Keep modules independent.
4. Do not introduce UI before Core works.
5. Do not replace architecture without a new ADR.