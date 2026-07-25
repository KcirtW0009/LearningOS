---
id: LOS-0402
title: Command Interface
status: Draft
version: 0.1.0
owner: Learning OS
last_updated: 2026-07-12

depends_on:
  - LOS-0400
  - LOS-0401
  - LOS-0200

referenced_by:
  - LOS-0403
  - LOS-0404
  - LOS-0405

applicable_articles: []
---

# Command Interface

## Purpose

This document defines the first interaction interface between users and the Learning OS Runtime.

The Command Interface provides a stable boundary between external interaction methods and internal Runtime components.

---

# Design Principle

The Command Interface follows:

```
User Interaction

        ↓

Command Layer

        ↓

Runtime Core
```

---

# Interface Responsibility

The Command Interface is responsible for:

- receiving user commands;
- validating command parameters;
- invoking Runtime operations;
- displaying results.

---

# Non-Responsibilities

The Command Interface MUST NOT:

- implement Graph logic;
- modify State directly;
- contain persistence logic.

---

# Initial Interface

The first Runtime prototype uses:

```
Command Line Interface (CLI)
```

Reason:

- simple;
- reproducible;
- easy to test;
- suitable for prototype validation.

---

# Command Structure

General format:

```
los <resource> <action> [options]
```

Example:

```
los graph load ai-roadmap
```

---

# Core Commands

The initial Runtime SHOULD support:

```
graph

node

state

status

config
```

---

# Graph Commands

## Load Graph

Command:

```
los graph load <package>
```

Purpose:

Load a Learning Graph Package.

Example:

```
los graph load ai-engineer-roadmap
```

---

## Graph Information

Command:

```
los graph info
```

Purpose:

Display current Graph information.

Example output:

```
Graph:

AI Engineer Roadmap

Version:

1.0.0
```

---

# Node Commands

## List Nodes

Command:

```
los node list
```

Purpose:

Display available Nodes.

Example:

```
Available Nodes:

1. Python Basics

2. Linear Algebra

3. Neural Networks
```

---

## Node Information

Command:

```
los node info <node_id>
```

Purpose:

Display Node details.

---

## Complete Node

Command:

```
los node complete <node_id>
```

Purpose:

Update user progress.

Example:

```
los node complete python-basics
```

---

# State Commands

## Show Status

Command:

```
los status
```

Purpose:

Display current learning progress.

Example:

```
Completed:

5 / 100 Nodes
```

---

## Export State

Command:

```
los state export
```

Purpose:

Export user progress.

---

## Import State

Command:

```
los state import <file>
```

Purpose:

Restore user progress.

---

# Validation Rules

Commands MUST:

- provide clear errors;
- avoid destructive actions by default;
- preserve user data.

---

# Error Handling

Errors SHOULD provide:

- problem description;
- possible solution;
- affected resource.

Example:

```
Graph package not found.

Check package path.
```

---

# Future Interfaces

The Command Interface SHOULD allow future replacement by:

## Desktop Interface

```
Desktop UI

        ↓

Command Layer
```

---

## Web Interface

```
Web Client

        ↓

API Adapter

        ↓

Command Layer
```

---

## AI Interface

```
AI Agent

        ↓

Command Layer
```

---

# Command Versioning

Commands MAY evolve.

Breaking changes SHOULD:

- update interface version;
- provide migration information.

---

# Security Considerations

Commands that modify user data SHOULD:

- require explicit confirmation;
- prevent accidental deletion.

---

# Example Workflow

A typical learning session:

```
1.

Load Graph


los graph load ai-roadmap


2.

Check available Nodes


los node list


3.

Study and complete Node


los node complete python-basics


4.

Check progress


los status
```

---

# Acceptance Criteria

This document is complete when:

- external interaction boundary is defined;
- CLI prototype commands are specified;
- future UI expansion remains possible.

---

# Next Document

Continue reading:

**LOS-0403 — Graph Engine**

---

# Agent Note

When implementing commands:

1. Commands are interfaces, not business logic.
2. Keep Runtime Core independent.
3. CLI is only the first adapter.
4. Future interfaces must reuse the same command model.