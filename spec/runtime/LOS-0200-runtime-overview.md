---
id: LOS-0200
title: Runtime Overview
status: Draft
version: 0.1.0
owner: Learning OS
last_updated: 2026-07-12

depends_on:
  - LOS-0000
  - LOS-0100
  - LOS-0102

referenced_by:
  - LOS-0201
  - LOS-0202
  - LOS-0203

applicable_articles: []
---

# Runtime Overview

## Purpose

This document defines the responsibilities and boundaries of the Learning OS Runtime.

The Runtime is the execution environment of Learning OS.

It loads Learning Graphs, manages user state, and provides interaction between users and learning structures.

---

# Runtime Definition

The Runtime is a generic execution system that interprets Learning Graph data and manages learning progress.

The Runtime does not contain domain-specific knowledge.

---

# Runtime Responsibilities

The Runtime MUST provide the following capabilities.

---

## Graph Loading

The Runtime MUST be able to load valid Learning Graph packages.

Responsibilities:

- read Graph definitions;
- validate Graph structure;
- initialize learning environment.

---

## State Management

The Runtime MUST maintain user-specific learning state.

Responsibilities:

- track completed Nodes;
- store scores;
- record progress;
- manage learning status.

---

## Progress Persistence

The Runtime MUST provide persistent storage for user data.

User progress MUST survive:

- application restart;
- Graph updates;
- Runtime updates.

---

## Graph Execution

The Runtime interprets relationships defined by Graphs.

Examples:

- prerequisite checking;
- Node availability;
- progression calculation.

---

## User Interaction

The Runtime provides interfaces for users to:

- view learning structures;
- update progress;
- record evidence;
- inspect history.

---

# Runtime Non-Responsibilities

The Runtime MUST NOT:

## Contain Domain Knowledge

Runtime should not include:

- AI knowledge;
- programming knowledge;
- mathematics knowledge.

---

## Generate Learning Content

Runtime does not create:

- courses;
- explanations;
- tutorials.

---

## Automatically Judge Mastery

Runtime does not determine whether a user truly understands a topic.

---

## Depend on External AI

AI systems may extend Runtime functionality but cannot become required dependencies.

---

# Runtime Architecture Model

The conceptual model is:

```
+-------------------+

 User Interface

+-------------------+

          |

          v

+-------------------+

 Runtime

+-------------------+

          |

          v

+-------------------+

 Learning Graph

+-------------------+

          |

          v

+-------------------+

 User Progress

+-------------------+
```

---

# Runtime Components

The Runtime is conceptually divided into:

## Graph Layer

Responsible for:

- loading Graph data;
- interpreting Nodes;
- resolving relationships.

---

## State Layer

Responsible for:

- storing progress;
- managing completion;
- tracking user status.

---

## Storage Layer

Responsible for:

- persistence;
- local data management.

---

## Presentation Layer

Responsible for:

- visualization;
- interaction.

---

# Runtime Determinism

Given:

- identical Graph data;
- identical user state;
- identical Runtime version;

the Runtime SHOULD produce identical results.

---

# Runtime Extension

Extensions MAY add:

- visualization;
- external tools;
- AI assistance;
- synchronization.

Extensions MUST NOT violate Runtime principles.

---

# Acceptance Criteria

This document is complete when:

- Runtime responsibility boundaries are clear;
- Runtime non-responsibilities are defined;
- future Runtime specifications have a clear foundation.

---

# Next Document

Continue reading:

**LOS-0201 — State Model**

---

# Agent Note

When implementing Runtime:

1. Do not add domain knowledge.
2. Do not hardcode Graph content.
3. Follow Runtime specifications before writing code.