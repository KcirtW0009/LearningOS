---
id: LOS-0302
title: Edge Model
status: Draft
version: 0.1.0
owner: Learning OS
last_updated: 2026-07-12

depends_on:
  - LOS-0300
  - LOS-0301

referenced_by:
  - LOS-0303
  - LOS-0304

applicable_articles: []
---

# Edge Model

## Purpose

This document defines the relationship model between Nodes inside a Learning Graph.

The Edge Model describes how learning elements connect and how progression relationships are represented.

---

# Definition

An Edge represents a relationship between two or more Nodes.

An Edge describes:

- connection;
- dependency;
- progression;
- association.

---

# Core Principle

Edges are Graph-level information.

They describe relationships between learning elements.

Edges do not represent user progress.

---

# Edge Structure

Conceptually:

```
Edge

+----------------+

| Source Node    |

+----------------+

| Target Node    |

+----------------+

| Relation Type  |

+----------------+

| Metadata       |

+----------------+

| Conditions     |

+----------------+
```

---

# Required Properties

Every Edge MUST define:

## Source

The starting Node.

Example:

```
python-basics
```

---

## Target

The connected Node.

Example:

```
pytorch-basics
```

---

## Relation Type

The semantic meaning of the relationship.

Example:

```
prerequisite
```

---

# Relation Type

Relation Type defines what an Edge means.

Runtime MUST treat Relation Type as extensible metadata.

---

# Core Relation Types

Learning OS defines several recommended relation types.

---

# Prerequisite

## Meaning

The source Node is required before the target Node.

Example:

```
Python Basics

        prerequisite

Deep Learning Framework
```

---

# Dependency

## Meaning

The target Node depends on the source Node.

Similar to prerequisite but may represent broader requirements.

---

# Progression

## Meaning

Represents a natural learning sequence.

Example:

```
Beginner Python

        progression

Advanced Python
```

---

# Association

## Meaning

Represents a related concept.

Example:

```
Computer Vision

        association

Image Processing
```

Association does not imply requirement.

---

# Alternative

## Meaning

Represents alternative learning paths.

Example:

```
TensorFlow

        alternative

PyTorch
```

---

# Edge Direction

Edges SHOULD have direction.

Example:

```
Node A

   |

   v

Node B
```

Direction provides interpretation.

---

# Directed Graph Principle

Learning Graphs are primarily directed graphs.

Direction enables:

- prerequisite resolution;
- progression calculation;
- path visualization.

---

# Edge Conditions

Edges MAY define conditions.

Examples:

## Score Requirement

```
Required score:

50
```

---

## Completion Requirement

```
Complete Node A
```

---

## Evidence Requirement

```
Submit project
```

---

# Condition Responsibility

Conditions are interpreted by Runtime.

However:

Runtime MUST only execute declared rules.

Runtime MUST NOT invent hidden requirements.

---

# Edge Weight

Edges MAY define optional weights.

Possible usage:

- importance;
- recommendation priority;
- visualization.

Weight MUST NOT automatically represent user ability.

---

# Multiple Relationships

Two Nodes MAY have multiple Edges.

Example:

```
Node A

   |
   | prerequisite

   |
Node B


Node A

   |
   | association

   |
Node B
```

Different relations represent different meanings.

---

# Edge Versioning

Edges SHOULD support version tracking.

Changes MAY include:

- relation changes;
- condition updates;
- dependency updates.

---

# Edge Removal

Removing an Edge SHOULD consider existing User State.

A removed prerequisite should not silently invalidate historical progress.

---

# Graph Traversal

Runtime MAY use Edges to calculate:

- available Nodes;
- learning paths;
- dependencies.

---

# Edge Limitations

Edges MUST NOT:

- execute arbitrary logic;
- contain learning content;
- modify Runtime behavior.

---

# Community Extension

Communities MAY define new Relation Types.

Extensions SHOULD:

- provide clear semantics;
- avoid conflicting meanings;
- remain compatible with generic Runtime.

---

# Example

Example Graph:

```
Node:

Python Basics


Edge:

Source:

Python Basics


Relation:

prerequisite


Target:

PyTorch Fundamentals
```

Meaning:

Python Basics should be completed before PyTorch Fundamentals.

---

# Edge Design Principles

## Principle 1

Edges describe relationships, not actions.

---

## Principle 2

Relations should remain extensible.

---

## Principle 3

Graph defines possibilities.

User State defines reality.

---

# Acceptance Criteria

This document is complete when:

- Edge structure is defined;
- relationships are extensible;
- progression logic is separated from Runtime;
- future Graph packages can represent learning paths.

---

# Next Document

Continue reading:

**LOS-0303 — Graph Package**

---

# Agent Note

When implementing Edges:

1. Do not hardcode only one relationship type.
2. Do not mix Edge data with User progress.
3. Keep relations extensible.
4. Avoid turning Graph into executable workflows.