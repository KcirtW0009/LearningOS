---
id: LOS-0201
title: State Model
status: Draft
version: 0.1.0
owner: Learning OS
last_updated: 2026-07-12

depends_on:
  - LOS-0200
  - LOS-0102
  - LOS-0103

referenced_by:
  - LOS-0203

applicable_articles: []
---

# State Model

## Purpose

This document defines the user progress state model used by Learning OS Runtime.

The State Model describes how Runtime represents user interaction with Learning Graphs.

---

# Fundamental Separation

Learning OS separates:

```
Learning Graph

        +

User State
```

A Graph defines available learning structures.

A User State records individual learning history.

The Runtime MUST never modify Graph data to store user progress.

---

# User State Definition

User State is the complete representation of a user's current interaction with a Learning Graph.

A User State includes:

- identity information;
- Graph reference;
- Node progress;
- evidence records;
- timestamps;
- user-defined scores.

---

# State Ownership

User State belongs to the user.

The system MUST ensure:

- user data can be exported;
- user data can be backed up;
- user data can survive Graph replacement.

---

# State Structure

The conceptual structure:

```
User State

|

+-- User Profile

|

+-- Graph Reference

|

+-- Node States

|

+-- Evidence Records

|

+-- History Records
```

---

# Node State

## Definition

Node State represents the user's relationship with an individual Node.

Each Node State corresponds to a Node defined in a Graph.

---

# Node State Properties

A Node State MAY contain:

| Property | Description |
|-|-|
| node_id | Reference to Graph Node |
| status | Current learning status |
| score | User-defined progress value |
| evidence | Related learning evidence |
| updated_at | Last modification time |

---

# Node Status

The Runtime SHOULD support the following generic states.

```
Locked

↓

Available

↓

In Progress

↓

Completed

↓

Mastered
```

---

# Locked

## Definition

The Node cannot currently be started.

Possible reasons:

- prerequisites incomplete;
- Graph rules prevent access.

---

# Available

## Definition

The Node can be started by the user.

---

# In Progress

## Definition

The user has started learning the Node.

---

# Completed

## Definition

The user considers the Node completed.

Completion is a user-defined decision.

---

# Mastered

## Definition

The user considers the Node sufficiently understood or practiced.

Mastery does not imply automatic verification.

---

# Score Model

Learning OS supports numerical progress representation.

Example:

```
0

Not Started


10

Completed


50

Proficient


100

Mastered
```

The Runtime stores scores.

The Runtime does not define universal score meanings.

---

# Evidence Model

Evidence is optional user-provided information.

Examples:

- notes;
- project links;
- documents;
- personal records.

Evidence helps users track learning history.

Evidence does not automatically validate capability.

---

# Progress Calculation

The Runtime MAY calculate:

- available Nodes;
- completion percentage;
- learning statistics.

The Runtime MUST NOT infer:

- intelligence;
- ability;
- true mastery.

---

# State Transition

State changes SHOULD follow explicit transitions.

Example:

```
Locked

    |
    v

Available

    |
    v

In Progress

    |
    v

Completed

    |
    v

Mastered
```

Unexpected transitions SHOULD be rejected.

---

# Graph Independence

When a Graph package changes:

The Runtime SHOULD attempt to preserve compatible User State.

Examples:

- unchanged Node IDs remain linked;
- removed Nodes become historical records;
- new Nodes start without progress.

---

# Export Requirements

The Runtime SHOULD allow users to export:

- Node progress;
- scores;
- evidence references;
- learning history.

Exported data SHOULD remain understandable without Runtime-specific information.

---

# Acceptance Criteria

This document is complete when:

- user progress is clearly separated from Graph data;
- Node state behavior is defined;
- state transitions are understandable;
- future storage design has a clear model.

---

# Next Document

Continue reading:

**LOS-0202 — Graph Loader**

---

# Agent Note

When implementing State:

1. Never store progress inside Graph files.
2. Never automatically judge mastery.
3. Preserve user ownership of data.