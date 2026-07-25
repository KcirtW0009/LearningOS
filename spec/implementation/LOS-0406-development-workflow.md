---
id: LOS-0406
title: Development Workflow
status: Draft
version: 0.1.0
owner: Learning OS
last_updated: 2026-07-12

depends_on:
  - LOS-0100
  - LOS-0102
  - LOS-0400
  - LOS-0401

referenced_by:
  - future implementation documents

applicable_articles: []
---

# Development Workflow

## Purpose

This document defines the development workflow for Learning OS implementation.

The purpose is to establish a consistent engineering process for:

- human contributors;
- AI coding agents;
- automated tools.

This document ensures that implementation remains aligned with the Learning OS specifications.

---

# Core Principle

Learning OS follows:

```
Specification First

        ↓

Implementation

        ↓

Verification

        ↓

Iteration
```

The specification is the primary source of truth.

Code exists to implement specifications.

---

# Development Roles

The project defines three major roles.

---

# Architecture Maintainer

Responsibility:

- maintain specifications;
- approve architectural changes;
- review ADR decisions.

The Architecture Maintainer decides:

```
What the system should become
```

---

# Implementation Agent

Includes:

- human developers;
- AI coding agents.

Responsibility:

- implement approved specifications;
- write tests;
- fix implementation issues.

The Implementation Agent decides:

```
How to implement within constraints
```

---

# Reviewer

Responsibility:

- verify implementation correctness;
- check specification compliance;
- prevent accidental architecture changes.

---

# Agent Operating Rules

Before modifying code, agents MUST:

1. Read relevant specifications.
2. Identify affected components.
3. Confirm dependency boundaries.
4. Understand acceptance criteria.

---

# Specification Priority

When conflicts occur:

The priority order is:

```
ADR

↓

Architecture Specification

↓

Implementation Specification

↓

Code

↓

Temporary Notes
```

Code MUST NOT override specifications silently.

---

# Implementation Scope

Each development task SHOULD have:

- clear objective;
- affected files;
- acceptance criteria.

Example:

```
Implement Graph Loader

Scope:

runtime/graph/

Related Spec:

LOS-0403
```

---

# Avoid Scope Expansion

Agents SHOULD NOT:

- redesign unrelated modules;
- introduce unnecessary dependencies;
- modify architecture without approval.

---

# Branch Strategy

Development SHOULD use:

```
main/master

        |

        |

feature branch
```

Example:

```
feature/runtime-graph-loader
```

---

# Commit Convention

Commits SHOULD follow:

```
type(scope): description
```

Examples:

```
feat(graph): implement node loader

feat(state): add progress update

fix(storage): repair json migration

docs(spec): update runtime specification

test(graph): add validation tests
```

---

# Commit Principles

A commit SHOULD:

- represent one meaningful change;
- be easy to review;
- keep the project runnable.

---

# Testing Requirement

Every implementation feature SHOULD include tests.

Minimum requirements:

```
Implementation

        +

Test

        +

Documentation Update(if needed)
```

---

# Prototype Testing Priority

During early stages:

Priority order:

```
Correctness

        >

Maintainability

        >

Performance
```

---

# Code Review Checklist

Reviewers SHOULD check:

## Architecture

- Does the code follow specifications?
- Are responsibilities separated?

---

## Data Model

- Are Node IDs preserved?
- Is Graph separated from State?

---

## Storage

- Is user data protected?
- Is migration possible?

---

## Dependencies

- Are new dependencies necessary?
- Do they increase complexity?

---

# AI Coding Rules

AI agents MUST:

## Read Before Write

Never generate implementation without reading related specifications.

---

## Explain Changes

Before major modifications, provide:

- changed files;
- reason;
- affected modules.

---

## Avoid Hidden Decisions

AI agents MUST NOT silently decide:

- new architecture;
- new data model;
- new dependency.

Such decisions require documentation.

---

# Pull Request Requirements

A completed change SHOULD include:

```
Summary

Changed Files

Testing Result

Potential Risks
```

---

# Error Handling Workflow

When implementation conflicts with specification:

The agent SHOULD:

```
Stop

↓

Report Conflict

↓

Request Decision

↓

Continue
```

The agent SHOULD NOT:

```
Modify Specification Automatically
```

---

# Versioning Workflow

Version progression:

```
Development

↓

Prototype

↓

Stable Release
```

Example:

```
v0.5.0-first-runtime
```

---

# Documentation Synchronization

When implementation changes architecture:

The developer MUST update:

- related Spec;
- ADR if necessary.

Code and Specification MUST remain synchronized.

---

# First Implementation Target

The first implementation milestone:

```
v0.5.0-first-runtime
```

Minimum capability:

```
Load Graph

↓

Query Nodes

↓

Update State

↓

Save Progress
```

---

# Non-Goals

This workflow does not define:

- UI development process;
- community contribution process;
- AI service integration.

These will be defined in future specifications.

---

# Acceptance Criteria

This document is complete when:

- development roles are clear;
- Agent workflow is defined;
- commit rules are established;
- implementation boundaries are protected.

---

# Agent Note

Learning OS is a specification-driven project.

The correct workflow is:

Read → Understand → Implement → Test → Document → Commit

Do not skip specification reading.