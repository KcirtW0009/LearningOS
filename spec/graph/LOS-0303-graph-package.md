---
id: LOS-0303
title: Graph Package
status: Draft
version: 0.1.0
owner: Learning OS
last_updated: 2026-07-12

depends_on:
  - LOS-0300
  - LOS-0301
  - LOS-0302

referenced_by:
  - LOS-0304

applicable_articles: []
---

# Graph Package

## Purpose

This document defines the packaging model of Learning Graphs.

A Graph Package is the distributable unit of Learning OS knowledge structures.

---

# Definition

A Graph Package is a self-contained collection of files that describes a Learning Graph.

A Graph Package contains:

- Graph metadata;
- Node definitions;
- Edge definitions;
- optional resources;
- extension information.

---

# Core Principle

Graph Packages are data packages.

They MUST NOT contain executable behavior.

---

# Package Responsibilities

A Graph Package SHOULD provide:

- identity information;
- version information;
- Graph structure;
- learning resources;
- extension metadata.

---

# Package Non-Responsibilities

A Graph Package MUST NOT contain:

- user progress;
- personal notes;
- private evidence;
- Runtime configuration;
- executable scripts.

---

# Package Structure

A conceptual Graph Package:

```
graph-package/

|

+-- manifest.yaml

|

+-- graph.yaml

|

+-- nodes/

|

+-- edges/

|

+-- resources/

|

+-- extensions/
```

---

# Manifest

## Definition

The Manifest describes package-level information.

Example:

```
name:

AI Engineer Roadmap


version:

1.0.0


author:

community-user
```

---

# Required Manifest Information

A Manifest SHOULD contain:

## Package ID

Unique identifier.

---

## Package Name

Human-readable name.

---

## Version

Current package version.

---

## Author

Creator or maintainer information.

---

## Compatibility

Runtime compatibility information.

---

# Graph Definition

The Graph definition describes:

- Nodes;
- Edges;
- structure information.

The exact schema is defined by:

```
LOS-0301 Node Model

LOS-0302 Edge Model
```

---

# Node Storage

Nodes MAY be stored:

- in a single file;
- in multiple files.

Implementation choice SHOULD NOT affect the Graph Model.

---

# Edge Storage

Edges MAY be stored:

- in a single file;
- in multiple files.

---

# Resource Storage

Packages MAY include resources.

Examples:

- references;
- documentation links;
- learning materials.

Resources SHOULD remain optional.

---

# Resource Independence

Learning OS SHOULD NOT require resources to exist locally.

A missing resource MUST NOT invalidate Graph structure.

---

# Package Versioning

Every Graph Package SHOULD define versions.

Versioning SHOULD describe:

- structural changes;
- content changes;
- compatibility changes.

---

# Version Compatibility

A Runtime SHOULD determine whether:

- a package can be loaded;
- migration is required;
- manual intervention is needed.

---

# Package Updates

When a new package version is installed:

The Runtime SHOULD:

- preserve compatible User State;
- identify changed Nodes;
- maintain history.

---

# User State Relationship

Graph Package:

```
defines:

Node A exists
```

User State:

```
records:

User completed Node A
```

They remain independent.

---

# Package Import

The import process:

```
Receive Package

        |

        v

Validate Manifest

        |

        v

Validate Graph Structure

        |

        v

Load Graph

        |

        v

Connect Existing User State
```

---

# Package Export

The Runtime SHOULD allow exporting compatible Graph Packages.

Exported packages SHOULD:

- contain required metadata;
- remain portable;
- not include private user information.

---

# Security Considerations

Graph Packages are external data.

Runtime SHOULD:

- validate input;
- reject malformed structures;
- avoid executing package contents.

---

# Community Distribution

Community members MAY distribute Graph Packages through:

- Git repositories;
- package repositories;
- file sharing.

A valid package SHOULD be usable by any compatible Runtime.

---

# Forking and Modification

Users MAY create modified versions of existing Graph Packages.

Modified packages SHOULD:

- preserve original attribution;
- update version information;
- describe changes.

---

# Package Compatibility

Future Runtime versions SHOULD maintain backward compatibility where possible.

Breaking changes SHOULD:

- update specification versions;
- provide migration guidance.

---

# Example

A package:

```
AI-Engineer-Roadmap

version:

1.0.0
```

contains:

```
Nodes:

Python Basics

Linear Algebra

Neural Networks


Edges:

Python Basics

        prerequisite

Neural Networks
```

The Runtime loads the package.

The user's progress remains separate.

---

# Design Principles

## Principle 1

Packages describe knowledge, not execution.

---

## Principle 2

Packages are portable.

---

## Principle 3

User data never belongs inside packages.

---

## Principle 4

Community-created packages are first-class citizens.

---

# Acceptance Criteria

This document is complete when:

- Graph Package responsibilities are defined;
- package structure is clear;
- distribution model is established;
- community extension is possible.

---

# Next Document

Continue reading:

**LOS-0304 — Extension Model**

---

# Agent Note

When implementing Graph Packages:

1. Treat packages as data.
2. Never execute package content.
3. Preserve user state separately.
4. Design for community sharing.