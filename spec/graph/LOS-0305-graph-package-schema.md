---
id: LOS-0305
title: Graph Package Schema
status: Draft
version: 0.1.0
owner: Learning OS
last_updated: 2026-07-12

depends_on:
  - LOS-0301
  - LOS-0302
  - LOS-0303

referenced_by:
  - LOS-0500

applicable_articles: []
---

# Graph Package Schema

## Purpose

This document defines the concrete YAML schema for Learning Graph Package files used by the v0.5.0 Runtime prototype.

The schema defines the minimal fields required to create a valid, loadable Graph Package.

This document does not define Extension schemas, Visualization schemas, or future advanced formats.

---

# Design Principle

The v0.5.0 schema follows:

```
Minimal Required Fields

        +

Stable Node Identity

        +

Predictable Parser Behavior
```

---

# Package Structure

A v0.5.0 Graph Package MUST contain two files:

```
graph-package/
│
├── manifest.yaml
│
└── graph.yaml
```

`manifest.yaml` describes package-level metadata.

`graph.yaml` contains all Node and Edge definitions in a single file.

Multi-file layouts (`nodes/`, `edges/` subdirectories) are reserved for future versions.

---

# manifest.yaml

## Purpose

The manifest identifies the package and declares compatibility.

## Schema

```yaml
package_id: ai-engineer-roadmap
name: AI Engineer Roadmap
version: 1.0.0
author: community-user
compatibility:
  runtime: ">=0.5.0"
  schema: "1.0.0"
```

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `package_id` | string | Unique identifier. Lowercase, hyphen-separated. |
| `name` | string | Human-readable package name. |
| `version` | string | Semantic version of this package. |

## Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `author` | string | Creator or maintainer identifier. |
| `compatibility` | mapping | Runtime and schema version requirements. |

## Compatibility Block

If present, `compatibility` MAY contain:

| Field | Type | Description |
|-------|------|-------------|
| `runtime` | string | Minimum Runtime version. |
| `schema` | string | Schema version used by this package. |

---

# graph.yaml

## Purpose

The graph file defines all Nodes and Edges that form the Learning Graph.

## Schema Structure

```yaml
nodes:
  - id: python-basics
    title: Python Basics
    description: Fundamental Python programming concepts.
    type: concept
    difficulty: beginner

  - id: pytorch-basics
    title: PyTorch Fundamentals
    description: Introduction to PyTorch framework.
    type: concept
    difficulty: beginner

edges:
  - from: python-basics
    to: pytorch-basics
    relation: prerequisite
```

---

# Node Definition

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Globally unique Node identifier. Lowercase, hyphen-separated. |
| `title` | string | Human-readable name. |
| `description` | string | Explanation of what this Node represents. |

## Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Semantic classification. Examples: `concept`, `skill`, `project`, `milestone`. |
| `difficulty` | string | Learning complexity. Examples: `beginner`, `intermediate`, `advanced`. |

## Node ID Rules

- Node IDs MUST be unique within a package.
- Node IDs SHOULD use lowercase letters, digits, and hyphens only.
- Node IDs SHOULD remain stable across package versions.
- Changing a Node ID is equivalent to creating a new Node.

---

# Edge Definition

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `from` | string | Source Node ID. |
| `to` | string | Target Node ID. |
| `relation` | string | Relationship type. |

## Relation Types

The v0.5.0 Runtime MUST recognize:

| Relation | Meaning |
|----------|---------|
| `prerequisite` | Source Node must be completed before Target Node becomes available. |
| `dependency` | Target Node depends on Source Node. Same availability semantics as prerequisite. |
| `progression` | Natural learning sequence. Source completed → Target available. |
| `association` | Related concept. Does NOT affect availability. |
| `alternative` | Alternative learning path. Does NOT affect availability. |

## Edge Validation Rules

- `from` MUST reference an existing Node ID in the same package.
- `to` MUST reference an existing Node ID in the same package.
- Duplicate Edges (same `from`, `to`, `relation`) SHOULD be rejected.

---

# Complete Example

A minimal valid package:

### manifest.yaml

```yaml
package_id: example-basics
name: Example Basics
version: 1.0.0
```

### graph.yaml

```yaml
nodes:
  - id: node-a
    title: Node A
    description: First learning unit.

  - id: node-b
    title: Node B
    description: Second learning unit.

edges:
  - from: node-a
    to: node-b
    relation: prerequisite
```

---

# Parser Behavior

## Loading Order

```
Read manifest.yaml
        ↓
Validate manifest required fields
        ↓
Read graph.yaml
        ↓
Parse all Nodes
        ↓
Parse all Edges
        ↓
Validate Edge references
        ↓
Build Runtime Graph Model
```

## Error Handling

If any required field is missing:

```
Graph package validation failed: missing required field '<field>' in manifest.yaml
```

If any Edge references an unknown Node:

```
Edge references unknown Node: '<node_id>'
```

The Runtime MUST reject invalid packages without side effects.

---

# Out of Scope

The v0.5.0 schema does NOT define:

- Extension data structures
- Visualization metadata
- Task/assessment schemas
- Evidence requirement schemas
- Multi-file or multi-package graphs
- Node versioning or deprecation markers
- Edge condition expressions
- Resource references

These are reserved for future specification versions.

---

# Schema Versioning

This document defines schema version `1.0.0`.

Future changes to the schema SHOULD:

- increment the schema version;
- maintain backward compatibility where possible;
- update this document.

---

# Acceptance Criteria

This document is complete when:

- manifest.yaml fields are explicitly defined;
- graph.yaml Node and Edge fields are explicitly defined;
- edge relation types are enumerated;
- parser behavior for v0.5.0 is unambiguous;
- out-of-scope items are documented.

---

# Next Document

Continue reading:

**LOS-0500 — First Runtime Implementation**

---

# Agent Note

When implementing the parser:

1. Treat missing required fields as hard errors.
2. Use Node ID as the primary key, not title.
3. Do not add fields beyond this schema.
4. Reject unknown relation types with a clear error.
5. Schema is data — do not execute Graph content.
