---
id: LOS-0404
title: State Engine
status: Draft
version: 0.1.0
owner: Learning OS
last_updated: 2026-07-12

depends_on:
  - LOS-0201
  - LOS-0400
  - LOS-0403

referenced_by:
  - LOS-0405

applicable_articles: []
---

# State Engine

## Purpose

This document defines the behavior and responsibility of the State Engine inside Learning OS Runtime.

The State Engine manages user-specific learning progress while keeping user data independent from Learning Graph definitions.

---

# Definition

The State Engine represents the current relationship between:

```
User

+

Learning Graph

+

Learning Progress
```

---

# Core Principle

The State Engine answers:

```
What has the user done?
```

It does not answer:

```
What should the user learn?
```

or:

```
Has the user truly mastered something?
```

---

# Responsibilities

The State Engine is responsible for:

- storing Node progress;
- updating learning status;
- recording user evidence;
- calculating user-visible statistics.

---

# Non-Responsibilities

The State Engine MUST NOT:

- modify Graph definitions;
- automatically judge mastery;
- generate learning paths;
- require AI services.

---

# State Model

A User State contains:

```
User State

+----------------+

| Metadata       |

+----------------+

| Node States    |

+----------------+

| History        |

+----------------+

| Evidence       |

+----------------+
```

---

# Node State

Each Node may have a corresponding User State entry.

Example:

```
Node:

transformer-attention


State:

{
 status: completed,
 score: 10
}
```

---

# Status Model

The initial status model:

```
NOT_STARTED

        |

IN_PROGRESS

        |

COMPLETED

        |

MASTERED
```

---

# Score System

The Runtime MAY support numerical scoring.

Example:

```
0

Not Started


10

Completed


50

Mastered
```

The scoring interpretation is user-defined.

The Runtime MUST NOT claim that a score represents objective ability.

---

# User Controlled Verification

Completion verification follows:

```
User Learning

      +

User Evidence

      +

User Confirmation

      ↓

State Update
```

---

# Evidence Model

Evidence is optional user-provided information.

Examples:

- project files;
- notes;
- reports;
- links;
- screenshots.

The Runtime stores references.

The Runtime does not verify authenticity.

---

# Evidence Structure

Conceptually:

```
Evidence

+----------------+

| Type           |

+----------------+

| Location       |

+----------------+

| Description    |

+----------------+
```

---

# Progress History

The State Engine SHOULD record important changes.

Example:

```
Node:

python-basics


History:

2026-07-12

score changed:

0 -> 10
```

---

# Available Node Calculation

The State Engine MAY request Graph Engine information.

Example:

```
Graph:

Python Basics

↓

PyTorch Basics


State:

Python Basics completed


Result:

PyTorch Basics available
```

---

# Dependency Boundary

The State Engine may consume:

```
Graph Information
```

but MUST NOT modify:

```
Graph Data
```

---

# Import and Export

The State Engine SHOULD support:

## Export

Purpose:

- backup;
- sharing;
- migration.

---

## Import

Purpose:

- restore;
- continue learning.

---

# Graph Replacement Compatibility

When users replace Graph Packages:

The State Engine SHOULD preserve existing data when:

- Node IDs remain unchanged;
- State schema remains compatible.

Example:

Old Graph:

```
python-basics
```

New Graph:

```
python-basics
```

Existing progress remains.

---

# Unknown Nodes

If a Graph no longer contains a previously completed Node:

The Runtime SHOULD:

- preserve historical data;
- mark it as orphaned.

---

# Privacy Principle

User State belongs to the user.

The system MUST:

- store locally by default;
- avoid unnecessary transmission.

---

# Future Extensions

Possible future additions:

- achievement system;
- XP system;
- badges;
- learning statistics.

These SHOULD be implemented as extensions.

---

# Acceptance Criteria

This document is complete when:

- user progress model is defined;
- Graph and State are separated;
- verification responsibility is clear;
- future gamification is possible.

---

# Next Document

Continue reading:

**LOS-0405 — Storage Adapter**

---

# Agent Note

When implementing State Engine:

1. Never modify Graph data.
2. Never fake mastery evaluation.
3. User owns progress data.
4. Keep scoring flexible.
5. Preserve history.