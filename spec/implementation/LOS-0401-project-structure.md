---
id: LOS-0401
title: Project Structure
status: Draft
version: 0.1.0
owner: Learning OS
last_updated: 2026-07-12

depends_on:
  - LOS-0400
  - LOS-0200
  - LOS-0300

referenced_by:
  - LOS-0402
  - LOS-0403
  - LOS-0404
  - LOS-0405

applicable_articles: []
---

# Project Structure

## Purpose

This document defines the initial repository structure and code organization principles for the Learning OS Runtime prototype.

The goal is to establish a stable engineering foundation before implementation begins.

---

# Design Principle

The project structure follows:

```
Separate Responsibilities

        +

Minimal Coupling

        +

Future Extension
```

---

# Repository Structure

The initial implementation SHOULD follow:

```
learning-os/

|

├── spec/

|

├── runtime/

|

├── graphs/

|

├── data/

|

├── examples/

|

├── tests/

|

├── docs/

|

├── scripts/

|

├── README.md

|

└── LICENSE
```

---

# Directory Responsibilities

## spec/

Purpose:

Store all specification documents.

Contains:

- architecture specifications;
- implementation specifications;
- protocols.

Runtime code MUST NOT depend on files inside spec/.

---

# runtime/

Purpose:

Contains Learning OS Runtime implementation.

This is the core executable system.

Suggested structure:

```
runtime/

├── graph/

├── state/

├── storage/

├── engine/

├── interface/

└── main.py
```

---

# runtime/graph/

Responsibility:

Handle Graph-related operations.

Includes:

- loading Graph Packages;
- parsing Nodes;
- parsing Edges;
- graph validation.

Must NOT:

- store user progress;
- modify user data.

---

# runtime/state/

Responsibility:

Handle learner state.

Includes:

- progress tracking;
- completion status;
- evidence references.

Must remain independent from Graph files.

---

# runtime/storage/

Responsibility:

Handle persistence.

Includes:

- saving state;
- loading state;
- storage migration.

---

# runtime/engine/

Responsibility:

Provide core interpretation logic.

Includes:

- dependency calculation;
- available Node detection;
- rule evaluation.

---

# runtime/interface/

Responsibility:

Provide interaction layer.

Possible implementations:

- CLI;
- local Web interface;
- Desktop interface.

Interface MUST NOT contain core business logic.

---

# graphs/

Purpose:

Store Learning Graph Packages.

Example:

```
graphs/

└── ai-engineer-roadmap/

    ├── manifest.yaml

    ├── nodes/

    └── edges/
```

Graph files represent knowledge structures.

They do not contain user progress.

---

# data/

Purpose:

Store local user data.

Example:

```
data/

└── user-state.json
```

This directory belongs to the user.

It MUST NOT be committed into public repositories.

---

# examples/

Purpose:

Provide example materials.

Includes:

- example Graph Packages;
- usage examples;
- demonstration data.

---

# tests/

Purpose:

Store automated tests.

Tests SHOULD cover:

- Graph loading;
- State updates;
- Storage operations.

---

# docs/

Purpose:

Store user-facing documentation.

Examples:

- tutorials;
- guides;
- explanations.

---

# scripts/

Purpose:

Store development utilities.

Examples:

- build scripts;
- validation scripts.

Scripts MUST NOT become Runtime dependencies.

---

# Dependency Direction

The project SHOULD follow:

```
interface

    ↓

engine

    ↓

graph / state

    ↓

storage
```

---

# Forbidden Dependencies

The following are prohibited:

## Graph depends on State

Reason:

Knowledge structure must remain independent.

---

## State depends on Interface

Reason:

User data should not depend on presentation.

---

## Runtime depends on Graph Content

Reason:

Runtime should remain generic.

---

# Configuration

Configuration SHOULD be separated from code.

Example:

```
config/

settings.yaml
```

---

# Extension Preparation

The structure SHOULD allow future additions:

```
plugins/

ui/

ai/
```

However these are not part of the first prototype.

---

# Development Environment

The first implementation SHOULD optimize for:

- local execution;
- simple setup;
- reproducibility.

---

# Acceptance Criteria

This document is complete when:

- directory responsibilities are defined;
- dependency boundaries are clear;
- future expansion remains possible.

---

# Next Document

Continue reading:

**LOS-0402 — Command Interface**

---

# Agent Note

When writing code:

1. Follow directory responsibility.
2. Do not move logic between layers casually.
3. Keep Graph, State, and Interface independent.
4. Prefer simple architecture over premature optimization.