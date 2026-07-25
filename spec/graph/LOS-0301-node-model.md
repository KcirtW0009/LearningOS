---
id: LOS-0301
title: Node Model
status: Draft
version: 0.1.0
owner: Learning OS
last_updated: 2026-07-12

depends_on:
  - LOS-0300
  - LOS-0201

referenced_by:
  - LOS-0303
  - LOS-0304

applicable_articles: []
---

# Node Model

## Purpose

This document defines the fundamental Node abstraction used by Learning OS Learning Graphs.

The Node Model describes how learning elements are represented, identified, and extended.

---

# Definition

A Node is the fundamental unit of a Learning Graph.

A Node represents an individual learning element.

Examples:

- a concept;
- a skill;
- a project;
- a milestone;
- an achievement.

---

# Core Principle

Learning OS Runtime MUST understand Node as a generic object.

Runtime MUST NOT depend on domain-specific Node categories.

---

# Node Independence

A Node describes learning structure.

A Node does not contain:

- personal progress;
- user scores;
- private evidence;
- completion history.

These belong to User State.

---

# Node Identity

Every Node MUST have a unique identifier.

Example:

```
node_id:
  ai.transformer.attention
```

---

# Node ID Requirements

Node IDs SHOULD be:

- globally unique;
- stable;
- human understandable;
- independent from display names.

---

# Node Identity Stability

A Node ID represents identity.

Changing:

- title;
- description;
- metadata;

does not necessarily create a new Node.

Changing the fundamental learning object MAY require a new Node ID.

---

# Node Structure

Conceptually:

```
Node

+----------------+

| Identity       |

+----------------+

| Metadata       |

+----------------+

| Requirements   |

+----------------+

| Resources      |

+----------------+

| Extensions     |

+----------------+
```

---

# Required Properties

Every Node MUST define:

## ID

Unique identifier of the Node.

---

## Title

Human-readable name.

Example:

```
Attention Mechanism
```

---

## Description

Explanation of what the Node represents.

---

# Optional Properties

A Node MAY define:

## Type

A descriptive classification.

Examples:

```
concept

skill

project

milestone
```

The Runtime MUST treat Type as metadata.

---

## Difficulty

A representation of learning complexity.

Example:

```
beginner

intermediate

advanced
```

Difficulty does not determine user ability.

---

## Estimated Effort

Optional estimation of required learning effort.

Example:

```
5 hours
```

---

## Resources

External learning references.

Examples:

- documents;
- websites;
- books;
- videos.

---

# Node Type

## Definition

Node Type describes the semantic category of a Node.

Node Type is metadata.

It is not a Runtime primitive.

---

# Examples

A Graph may define:

```
Type: Concept

"Transformer Architecture"
```

or:

```
Type: Project

"Implement GPT from Scratch"
```

Both remain:

```
Node
```

inside Runtime.

---

# Node Requirements

A Node MAY define requirements.

Requirements describe conditions before a Node becomes available.

Examples:

```
Required Node:

Python Basics
```

or:

```
Required Score:

50
```

---

# Node Completion

A Node MAY define completion criteria.

Examples:

- finish a task;
- submit evidence;
- reach a score.

Completion rules belong to Graph definitions.

The Runtime only evaluates defined rules.

---

# Node Evidence

A Node MAY specify expected evidence.

Examples:

- source code;
- notes;
- project files;
- reports.

Evidence records remain User Data.

---

# Node Extension

Nodes MAY contain extensions.

Extensions allow future expansion.

Examples:

- visualization data;
- external references;
- AI assistance metadata.

---

# Extension Rules

Extensions MUST:

- remain optional;
- not break Runtime compatibility;
- not replace core Node properties.

---

# Node Versioning

Nodes SHOULD support version tracking.

Changes MAY include:

- content updates;
- metadata changes;
- requirement changes.

---

# Node Deprecation

A deprecated Node SHOULD remain identifiable.

The system SHOULD preserve historical references.

Removing a Node MUST NOT silently destroy User State.

---

# Node Composition

Complex learning structures SHOULD be represented through relationships between Nodes.

Avoid creating large monolithic Nodes.

Example:

Instead of:

```
Machine Learning
```

as a single Node:

Prefer:

```
Machine Learning

    |

    +-- Linear Regression

    |

    +-- Neural Networks

    |

    +-- Optimization
```

---

# Node Design Principles

## Principle 1

Node is generic.

---

## Principle 2

Node identity is stable.

---

## Principle 3

Node content belongs to Graph.

Node progress belongs to User State.

---

## Principle 4

Extensions should not modify Runtime fundamentals.

---

# Acceptance Criteria

This document is complete when:

- Node is defined as the fundamental abstraction;
- Node structure is specified;
- Runtime independence is preserved;
- extension mechanisms are possible.

---

# Next Document

Continue reading:

**LOS-0302 — Edge Model**

---

# Agent Note

When creating Nodes:

1. Do not create domain-specific Runtime types.
2. Keep Node IDs stable.
3. Store learning history outside Nodes.
4. Use extensions instead of changing the core model.