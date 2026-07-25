---
id: LOS-0103
title: Glossary
status: Draft
version: 0.1.0
owner: Learning OS
last_updated: 2026-07-12

depends_on:
  - LOS-0100
  - LOS-0102

referenced_by:
  - LOS-0200
  - LOS-0300
  - LOS-0400

applicable_articles: []
---

# Glossary

## Purpose

This document defines the official terminology used throughout Learning OS specifications.

The purpose of this document is to ensure consistent understanding among:

- contributors;
- developers;
- AI agents;
- Graph creators;
- users.

When a term defined here is used in a Specification, it MUST follow this meaning.

---

# Core Terms

---

## Learning OS

### Definition

Learning OS is a local-first learning runtime that executes Learning Graphs and manages user progress.

### Not Definition

Learning OS is not:

- an AI tutor;
- an online course platform;
- an automatic evaluation system.

---

## Runtime

### Definition

Runtime is the executable component responsible for loading Graphs, managing states, and presenting learning progress.

### Rules

Runtime:

- understands generic structures;
- does not contain domain knowledge;
- does not define learning content.

---

## Graph

### Definition

A Graph is a structured representation of learning relationships.

A Graph describes:

- what can be learned;
- relationships between learning units;
- possible progression paths.

A Graph does not contain:

- personal progress;
- private user records.

---

## Graph Package

### Definition

A Graph Package is a distributable collection containing one or more Learning Graph definitions.

Examples:

- AI learning roadmap;
- programming curriculum;
- language learning path.

---

## Node

### Definition

A Node is the fundamental learning unit recognized by Learning OS.

A Node represents an individual element in a Learning Graph.

Examples:

- knowledge concept;
- skill;
- project;
- milestone;
- achievement.

---

## Edge

### Definition

An Edge represents a relationship between Nodes.

Edges define:

- dependency;
- sequence;
- relationship;
- progression.

---

## Task

### Definition

A Task is an actionable activity associated with a Node.

A Task describes how a learner may interact with a learning unit.

Examples:

- reading documentation;
- completing an implementation;
- building a project;
- writing notes.

---

## Progress

### Definition

Progress represents the user's current state within a Learning Graph.

Progress belongs to the user.

Progress does not belong to Graph packages.

---

## Evidence

### Definition

Evidence is user-provided material that records learning activities or achievements.

Examples:

- notes;
- documents;
- projects;
- links;
- files.

Evidence supports personal tracking.

It does not automatically prove mastery.

---

## Completion

### Definition

Completion is a user-defined state indicating that a learning requirement has been satisfied.

Completion is recorded by the system.

Completion is not automatically verified by the system.

---

## Score

### Definition

Score is a numerical representation used to describe user-defined progress or achievement levels.

Score meaning is determined by the relevant Graph specification.

The Runtime only stores and displays scores.

---

## Mastery

### Definition

Mastery represents a higher level of confidence or capability defined by the learner or Graph design.

Mastery is not automatically determined by Learning OS.

---

## Skill Tree

### Definition

A Skill Tree is a Graph representation that organizes learning progression through Nodes and relationships.

A Skill Tree is a visualization concept.

The underlying system abstraction remains Graph.

---

## Learning Path

### Definition

A Learning Path is a sequence or route through a Graph.

A Learning Path may be:

- predefined;
- generated;
- selected by users.

---

## User Profile

### Definition

User Profile stores information about the learner.

Examples:

- preferences;
- settings;
- identity information.

User Profile is separate from learning knowledge.

---

## User Data

### Definition

User Data includes all information created during personal use of Learning OS.

Examples:

- progress;
- evidence;
- settings;
- history.

User Data belongs to the user.

---

## External Tool

### Definition

An External Tool is a system that provides additional capabilities but is not required for core Runtime operation.

Examples:

- AI assistants;
- cloud services;
- synchronization systems.

---

## Specification

### Definition

Specification defines expected system behavior.

Specification has higher authority than implementation.

---

## Implementation

### Definition

Implementation is the concrete realization of Specifications through software, tools, or frameworks.

Implementation may change while Specifications remain stable.

---

# Naming Rules

The following naming rules SHOULD be followed.

## Learning Concepts

Use:

- Node
- Graph
- Task
- Progress

Avoid introducing unnecessary domain-specific runtime concepts.

---

## Technical Terms

Terms used in specifications SHOULD:

- have a single meaning;
- avoid ambiguity;
- be defined before use.

---

# Future Extensions

New terminology may be added when:

- a new concept becomes part of the official system;
- existing terminology becomes insufficient;
- the term is referenced by multiple Specifications.

New terms SHOULD be added here before being used widely.

---

# Acceptance Criteria

This document is complete when:

- core project terminology is defined;
- ambiguous concepts have clear meanings;
- future Specifications can reference consistent terminology.

---

# Next Document

Continue reading:

Governance layer completed.

Proceed to:

**Runtime Specifications**