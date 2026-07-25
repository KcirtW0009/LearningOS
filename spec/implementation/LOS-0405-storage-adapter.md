---
id: LOS-0405
title: Storage Adapter
status: Draft
version: 0.1.0
owner: Learning OS
last_updated: 2026-07-12

depends_on:
  - LOS-0203
  - LOS-0400
  - LOS-0404

referenced_by: []

applicable_articles: []
---

# Storage Adapter

## Purpose

This document defines the storage architecture of the Learning OS Runtime prototype.

The Storage Adapter provides persistence capability while maintaining separation between Runtime logic and storage implementation.

---

# Definition

The Storage Adapter is the boundary between Runtime components and persistent data.

Conceptually:

```
Runtime

    ↓

Storage Interface

    ↓

Storage Implementation
```

---

# Core Principle

Storage manages:

```
How data is saved
```

It does not manage:

```
What data means
```

---

# Responsibilities

The Storage Adapter is responsible for:

- reading data;
- writing data;
- validating stored format;
- handling persistence errors.

---

# Non-Responsibilities

Storage MUST NOT:

- calculate learning progress;
- interpret Graph relationships;
- decide Node completion.

---

# Initial Storage Implementation

The first prototype uses:

```
Local File Storage
```

Format:

```
JSON
```

Reason:

- human-readable;
- easy backup;
- easy debugging;
- simple migration.

---

# Storage Layout

Recommended:

```
data/

├── user-state.json

└── metadata.json
```

---

# User State Storage

Example:

```
user-state.json
```

contains:

```
{
 user_id,
 graph_reference,
 node_states,
 history
}
```

---

# Graph Reference

User State SHOULD record:

- Graph identifier;
- Graph version;
- Schema version.

Example:

```
{
 graph_id:
 "ai-engineer-roadmap",

 version:
 "1.0.0"
}
```

---

# Node Identity

Storage MUST use:

```
Node ID
```

as the primary reference.

Storage MUST NOT use:

- Node name;
- Display title.

---

# Reason

Names may change.

Example:

Before:

```
Deep Learning Introduction
```

After:

```
Introduction to Deep Neural Networks
```

The identity remains:

```
deep-learning-intro
```

---

# Graph Replacement

When replacing Graph Packages:

The Runtime SHOULD attempt:

```
Match Node ID

        ↓

Restore Existing State
```

---

# Compatible Replacement

Example:

Old:

```
python-basics
```

New:

```
python-basics
```

Result:

```
Progress preserved
```

---

# Incompatible Replacement

Example:

Old:

```
python-basics
```

New:

```
python-foundation-v2
```

Result:

```
Old history preserved

New Node starts empty
```

---

# Orphan State

If a Node disappears:

The Storage Adapter SHOULD preserve:

```
Historical State
```

Example:

```
orphaned_nodes
```

---

# Export

The system SHOULD support:

```
Export State
```

Purpose:

- backup;
- migration;
- sharing.

---

# Import

The system SHOULD support:

```
Import State
```

Requirements:

- validate schema;
- prevent corruption;
- provide errors.

---

# Version Management

Stored data SHOULD include:

```
schema_version
```

Example:

```
1.0.0
```

---

# Migration

Future versions MAY provide:

```
migration scripts
```

Example:

```
state v1

↓

state v2
```

---

# Data Ownership

User State belongs to the user.

The system SHOULD:

- keep data local;
- avoid hidden transmission;
- allow manual backup.

---

# Future Storage Options

The interface SHOULD allow:

## SQLite

For:

- larger datasets;
- search;
- analytics.

---

## Cloud Storage

Possible future:

- synchronization;
- multi-device support.

---

## Version Control

Possible future:

- Git-based learning history;
- change tracking.

---

# Acceptance Criteria

This document is complete when:

- storage boundary is defined;
- user data persistence is clear;
- Graph replacement behavior is defined;
- future migration is possible.

---

# Sprint Completion

After this document:

Sprint 4 Runtime Implementation Specification is complete.

---

# Agent Note

Implementation rules:

1. Never store Graph inside User State.
2. Always reference Node by ID.
3. Preserve user history.
4. Keep storage replaceable.
5. Local data belongs to the user.