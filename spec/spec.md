---
id: LOS-0000
title: Learning OS Specification Entry
status: Accepted
version: 0.1.0
owner: Learning OS
last_updated: 2026-07-12

depends_on: []

referenced_by:
  - LOS-0100

applicable_articles: []
---

# Learning OS Specification

## Purpose

This document is the single entry point for the Learning OS Specification.

Every contributor, AI coding agent, and implementation MUST read this document before reading any other specification.

The Learning OS Specification is the single source of truth (SSOT) for the project. Any implementation, tooling, or documentation MUST follow the Specification.

---

# Repository Structure

The repository is organized by responsibility.

```
LearningOS/

README.md

spec/
runtime/
graph/
examples/
user-data/
```

## Responsibilities

### spec/

Defines the behavior of the entire system.

Contains project governance, runtime specifications, graph specifications, gameplay rules, engineering standards, and future extension specifications.

No implementation should redefine any behavior described here.

---

### runtime/

Contains the implementation of the Learning OS Runtime.

The Runtime executes Learning Graphs and manages user progress.

The Runtime MUST NOT contain domain knowledge.

---

### graph/

Contains official Learning Graph packages.

Graphs describe knowledge structures.

Graphs are data.

Graphs are not executable code.

---

### examples/

Contains example Graph packages and demonstration projects.

Example content is informative only.

Examples never define system behavior.

---

### user-data/

Stores local user data.

This directory is intentionally excluded from version control.

User data belongs to the user.

---

# Specification Authority

The Specification is the highest authority of the project.

Whenever conflicts occur, the following priority order MUST be followed.

```
Specification
    ↑
Implementation
    ↑
Generated Content
```

Implementation MUST follow the Specification.

The Specification MUST NOT be changed to match existing code.

---

# Reading Order

Unless instructed otherwise, all readers should follow the reading order below.

```
LOS-0000
Specification Entry

↓

LOS-0100
Project Charter

↓

LOS-0101
Vision

↓

LOS-0102
Core Principles

↓

Remaining specifications
```

AI coding agents MUST follow the same reading order.

---

# Contribution Rules

All contributors SHOULD follow the rules below.

1. Read the relevant Specification before implementation.

2. If no Specification exists, create or update the Specification first.

3. Do not introduce undocumented behavior.

4. Do not modify Specifications indirectly through implementation.

5. Keep implementation consistent with the Specification.

---

# Scope

The Specification defines:

- project governance
- runtime behavior
- graph model
- gameplay rules
- persistence rules
- engineering standards
- AI agent workflow

The Specification does not define:

- implementation details
- framework selection
- UI style
- temporary experiments

---

# Terminology

The following terms are used throughout the project.

| Term | Meaning |
|------|---------|
| Runtime | The executable system that loads Graphs and manages user progress. |
| Graph | A structured representation of learning content. |
| Node | The smallest learning unit recognized by the Runtime. |
| Progress | User-owned learning state. |
| Specification | The authoritative project documentation. |

Additional terminology is defined in later specifications.

---

# Compliance

An implementation is considered Specification-compliant only if:

- Runtime behavior follows the Specification.
- Graphs conform to the Graph Specification.
- User Progress is stored independently from Graph data.
- Runtime contains no domain-specific knowledge.
- Local execution is fully supported.
- All implemented behavior is documented by the Specification.

---

# Next Document

Continue reading:

**LOS-0100 — Project Charter**

---

# Agent Note

If you are an AI coding assistant:

1. Read this document completely.

2. Continue with LOS-0100 before making implementation decisions.

3. Never assume undocumented behavior.

4. Report Specification conflicts instead of inventing new rules.