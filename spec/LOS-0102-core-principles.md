---
id: LOS-0102
title: Core Principles
status: Draft
version: 0.1.0
owner: Learning OS
last_updated: 2026-07-12

depends_on:
  - LOS-0100
  - LOS-0101

referenced_by:
  - LOS-0200
  - LOS-0300
  - LOS-0400
  - LOS-0500

applicable_articles: []
---

# Core Principles

## Purpose

This document defines the fundamental principles that guide all Learning OS design decisions.

These principles represent the stable foundation of the project.

All future specifications and implementations SHOULD remain consistent with these principles.

---

# Principle 1: Runtime Must Remain Generic

## Statement

The Learning OS Runtime MUST NOT contain domain-specific knowledge.

The Runtime only understands generic learning structures.

---

## Explanation

The Runtime should not know:

- artificial intelligence;
- programming languages;
- mathematics;
- science;
- professional skills.

The Runtime only understands concepts such as:

- Node;
- Graph;
- Task;
- Progress;
- State.

Knowledge belongs to Graph packages, not Runtime code.

---

# Principle 2: Knowledge Is Data

## Statement

Learning knowledge MUST be represented as external data.

Knowledge MUST NOT be hardcoded into the Runtime.

---

## Explanation

A new learning domain should be supported by creating a new Graph package.

Adding knowledge should not require modifying application code.

---

# Principle 3: User Progress Belongs to the User

## Statement

User progress MUST remain independent from Graph packages.

---

## Explanation

A Graph describes possible learning paths.

A user record describes individual learning history.

These two concepts must remain separated.

Updating, replacing, or sharing Graphs must not destroy user progress.

---

# Principle 4: Node Is the Fundamental Learning Unit

## Statement

Node is the smallest universal abstraction recognized by Learning OS.

---

## Explanation

Different learning concepts should be represented through Nodes.

Examples:

- skill;
- concept;
- project;
- milestone;
- achievement.

Specific Node categories may evolve.

The Runtime should not depend on domain-specific Node types.

---

# Principle 5: Learning Evaluation Is User Driven

## Statement

Learning OS records evaluation but does not become the authority of evaluation.

---

## Explanation

The system may provide:

- scoring mechanisms;
- completion states;
- evidence storage;
- progress visualization.

However, the learner remains responsible for determining achievement.

The Runtime does not automatically judge human capability.

---

# Principle 6: Local First

## Statement

Core Learning OS functionality MUST operate locally.

---

## Explanation

The following should remain available without external services:

- Graph loading;
- Progress storage;
- Learning history;
- Navigation.

External services may extend functionality but must not become mandatory.

---

# Principle 7: Deterministic Behavior

## Statement

Given identical Graph data and identical user state, the Runtime SHOULD produce identical results.

---

## Explanation

Learning progression should be understandable and reproducible.

The system should avoid hidden behavior caused by:

- opaque algorithms;
- external dependency;
- unpredictable services.

---

# Principle 8: Specification Before Implementation

## Statement

New behavior MUST be described by Specification before implementation.

---

## Explanation

Code implements defined behavior.

Code does not define system behavior.

If implementation requires a new capability, the Specification must be updated first.

---

# Principle 9: Portable Learning Structure

## Statement

Learning Graphs SHOULD remain independent from a specific Runtime implementation.

---

## Explanation

The same Graph package should be usable by different compatible implementations.

The user's learning structure should not be locked to one application.

---

# Principle 10: AI Is Optional

## Statement

Learning OS MUST remain functional without Large Language Models.

---

## Explanation

AI may provide additional capabilities.

Examples:

- explanation;
- assistance;
- analysis;
- generation.

However, AI is an external enhancement, not a core dependency.

---

# Principle Priority

When principles conflict, priority should generally follow:

```
User Ownership

↓

Runtime Independence

↓

Data Portability

↓

Extensibility

↓

Convenience
```

---

# Acceptance Criteria

This document is complete when:

- fundamental design rules are explicitly defined;
- future specifications can reference these principles;
- implementation decisions can be evaluated against these principles.

---

# Next Document

Continue reading:

**LOS-0103 — Glossary**

---

# Agent Note

Before implementing any feature:

1. Check whether the design follows these principles.
2. If a conflict exists, stop and request specification clarification.
3. Do not weaken principles to simplify implementation.