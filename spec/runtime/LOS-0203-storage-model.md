---
id: LOS-0203
title: Storage Model
status: Draft
version: 0.1.0
owner: Learning OS
last_updated: 2026-07-12

depends_on:
  - LOS-0200
  - LOS-0201
  - LOS-0202

referenced_by:
  - LOS-0300

applicable_articles: []
---

# Storage Model

## Purpose

This document defines the storage responsibilities and data separation model of Learning OS Runtime.

The Storage Model describes how Runtime persists user-owned information while maintaining independence between Graph data and User Data.

---

# Storage Principles

The Storage System MUST follow these principles:

- user data ownership;
- local-first operation;
- separation of concerns;
- data portability;
- recoverability.

---

# Storage Responsibilities

The Storage Layer is responsible for:

- persisting User State;
- loading saved progress;
- maintaining history records;
- supporting data export.

The Storage Layer is not responsible for:

- defining learning content;
- modifying Graph packages;
- evaluating user ability.

---

# Data Separation Model

Learning OS separates stored data into:

```
Graph Data

        +

User Data

        +

Runtime Metadata
```

---

# Graph Data

## Definition

Graph Data contains learning structure definitions.

Examples:

- Nodes;
- Edges;
- prerequisites;
- tasks;
- descriptions.

Graph Data is distributed through Graph Packages.

---

## Ownership

Graph Data belongs to:

- Graph creators;
- Graph maintainers;
- communities.

Graph Data does not contain private user progress.

---

# User Data

## Definition

User Data contains information generated through personal learning activity.

Examples:

- completed Nodes;
- scores;
- evidence;
- notes;
- learning history.

---

## Ownership

User Data belongs to the user.

The Runtime MUST NOT require external ownership of User Data.

---

# Runtime Metadata

## Definition

Runtime Metadata contains information required for application operation.

Examples:

- settings;
- local configuration;
- cache information.

Runtime Metadata should not contain essential learning records.

---

# Persistence Requirements

The Runtime SHOULD ensure:

## Durability

Saved progress survives:

- application restart;
- system restart;
- Runtime updates.

---

## Independence

User Data SHOULD remain usable when:

- Graph versions change;
- Runtime versions change;
- Graph packages are replaced.

---

## Exportability

Users SHOULD be able to export their learning data.

Exported data SHOULD include:

- progress;
- scores;
- evidence references;
- history.

---

# Storage Format Independence

The Specification does not require a specific storage technology.

Possible implementations include:

- file-based storage;
- embedded databases;
- other local persistence solutions.

The implementation choice MUST NOT affect the conceptual data model.

---

# Graph Update Handling

When Graph data changes:

The Storage Layer SHOULD preserve compatible User Data.

Examples:

## Node unchanged

Existing progress remains valid.

---

## Node removed

Historical progress should remain accessible.

---

## Node added

New Node starts without completion state.

---

## Node modified

Compatibility rules should determine migration behavior.

---

# Backup and Recovery

The Runtime SHOULD provide mechanisms to:

- backup User Data;
- restore previous states;
- prevent accidental data loss.

---

# Privacy

User Data SHOULD remain local by default.

External synchronization or sharing requires explicit user action.

---

# Storage Architecture Model

Conceptually:

```
+----------------+

 Graph Package

+----------------+

        |

        |

+----------------+

 Runtime

+----------------+

        |

        |

+----------------+

 User Storage

+----------------+
```

Graph Package and User Storage remain independent.

---

# Migration

Future Runtime versions MAY introduce storage migrations.

Migration systems MUST:

- preserve user progress;
- avoid silent data loss;
- provide clear migration behavior.

---

# Acceptance Criteria

This document is complete when:

- storage responsibilities are defined;
- Graph and User Data separation is explicit;
- user ownership requirements are established;
- future implementations have clear constraints.

---

# Next Document

Runtime Foundation completed.

Proceed to:

**Learning Graph Specification**

---

# Agent Note

When implementing Storage:

1. Never store user progress inside Graph packages.
2. Never make external services mandatory.
3. Protect user-owned learning history.