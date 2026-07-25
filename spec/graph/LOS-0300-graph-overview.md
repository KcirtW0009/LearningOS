---
id: LOS-0300
title: Graph Overview
status: Draft
version: 0.1.0
owner: Learning OS
last_updated: 2026-07-12

depends_on:
  - LOS-0100
  - LOS-0102
  - LOS-0103
  - LOS-0200

referenced_by:
  - LOS-0301
  - LOS-0302
  - LOS-0303
  - LOS-0304

applicable_articles: []
---

# Graph Overview

## Purpose

This document defines the fundamental concepts, responsibilities, and boundaries of Learning Graphs in Learning OS.

The purpose of this document is to establish a common understanding of how learning knowledge structures are represented.

This document does not define specific Graph file formats or implementation details.

---

# Definition

## Learning Graph

A Learning Graph is a structured representation of learning knowledge and progression relationships.

A Learning Graph describes:

- what can be learned;
- how learning units relate to each other;
- possible progression paths;
- optional learning requirements.

A Learning Graph does not describe:

- who is learning;
- user progress;
- personal achievements;
- private learning history.

---

# Core Concept

Learning OS separates learning systems into two independent layers:

```
Learning Graph

        +

User State
```

---

## Learning Graph

Represents:

"What exists in a learning domain?"

Examples:

- Artificial Intelligence roadmap;
- Programming language learning path;
- Mathematics curriculum.

---

## User State

Represents:

"What has a specific learner done?"

Examples:

- completed Nodes;
- personal scores;
- evidence;
- learning history.

---

# Graph Ownership

Learning Graphs are content structures.

Ownership belongs to:

- creators;
- maintainers;
- communities.

Learning Graphs may be:

- personal;
- private;
- shared;
- open-source.

---

# Runtime Relationship

The relationship between Runtime and Graph is:

```
              Graph Package

                    |

                    v

              Graph Loader

                    |

                    v

              Runtime Model

                    |

                    v

              User State
```

---

The Runtime interprets Graphs.

The Runtime does not define Graph meaning.

---

# Graph Responsibilities

A Learning Graph SHOULD define:

## Learning Units

Represented by Nodes.

Examples:

- concepts;
- skills;
- projects;
- milestones.

---

## Relationships

Represented by Edges.

Examples:

- prerequisite;
- dependency;
- progression;
- association.

---

## Learning Information

Examples:

- descriptions;
- references;
- suggested tasks;
- metadata.

---

# Graph Non-Responsibilities

A Learning Graph MUST NOT contain:

## Personal Progress

Examples:

- completion state;
- personal score;
- private notes.

These belong to User State.

---

## Executable Logic

Graph packages are data.

They MUST NOT contain:

- executable code;
- scripts;
- runtime modifications.

---

## External Authority

Graphs SHOULD NOT claim:

- automatic certification;
- guaranteed mastery;
- objective intelligence measurement.

---

# Graph as Data

Learning Graphs follow the principle:

> Knowledge is Data.

The Runtime consumes Graph data.

Adding new knowledge SHOULD be possible without modifying Runtime code.

---

# Graph Structure

At a conceptual level:

```
Learning Graph

+----------------+

| Metadata       |

+----------------+

        |

+----------------+

| Nodes          |

+----------------+

        |

+----------------+

| Edges          |

+----------------+

        |

+----------------+

| Extensions     |

+----------------+
```

---

# Node

## Definition

A Node is the fundamental unit inside a Learning Graph.

Nodes represent individual learning elements.

Examples:

- Attention Mechanism;
- Python Programming;
- Build a Neural Network Project.

Node details are defined in:

```
LOS-0301 Node Model
```

---

# Edge

## Definition

An Edge represents a relationship between Nodes.

Edges define how Nodes connect.

Examples:

```
Python Basics

        |

        v

Deep Learning Framework
```

Edge details are defined in:

```
LOS-0302 Edge Model
```

---

# Graph Package

## Definition

A Graph Package is a distributable unit containing a Learning Graph and its related resources.

A Graph Package may include:

- Graph definition files;
- metadata;
- documentation;
- references.

Graph Package details are defined in:

```
LOS-0303 Graph Package
```

---

# Versioning

Learning Graphs SHOULD support version management.

A Graph version identifies:

- structural changes;
- content updates;
- compatibility information.

---

# Graph Evolution

Learning Graphs are expected to evolve.

Possible changes:

## Add Node

A new learning element is introduced.

---

## Modify Node

Existing information changes.

---

## Remove Node

A learning element is deprecated.

---

## Modify Relationship

Learning dependencies change.

---

Graph evolution MUST consider existing User State.

---

# Community Extension

Learning OS supports community-created Graphs.

A community contributor MAY create:

- new Graph packages;
- domain-specific learning paths;
- alternative learning structures.

Community Graphs SHOULD:

- follow Graph specifications;
- define version information;
- avoid Runtime-specific dependencies.

---

# Graph Compatibility

A compatible Runtime SHOULD be able to:

- load valid Graph Packages;
- interpret Nodes and Edges;
- maintain User State independently.

---

# Graph Design Principles

Learning Graph design SHOULD follow:

## Principle 1

Keep knowledge structure separate from user progress.

---

## Principle 2

Use generic abstractions.

Avoid unnecessary domain-specific Runtime concepts.

---

## Principle 3

Prefer composability.

Graphs should be reusable and extendable.

---

## Principle 4

Preserve user history.

Graph evolution should not destroy learning records.

---

# Future Extensions

Future specifications MAY define:

- advanced Node types;
- visualization metadata;
- recommendation information;
- external resource references.

These extensions MUST preserve the core Graph model.

---

# Acceptance Criteria

This document is complete when:

- Graph responsibilities are defined;
- Graph boundaries are clear;
- Runtime and Graph separation is established;
- future Graph specifications have a stable foundation.

---

# Next Document

Continue reading:

**LOS-0301 — Node Model**

---

# Agent Note

When designing Graph structures:

1. Graph is data, not code.
2. Node is the fundamental abstraction.
3. User progress never belongs inside Graph.
4. Avoid creating domain-specific Runtime concepts.