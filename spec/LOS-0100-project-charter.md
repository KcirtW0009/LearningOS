---
id: LOS-0100
title: Project Charter
status: Draft
version: 0.1.0
owner: Learning OS
last_updated: 2026-07-12

depends_on:
  - LOS-0000

referenced_by:
  - LOS-0101
  - LOS-0102
  - LOS-0200
  - LOS-0300
  - LOS-0400

applicable_articles: []
---

# Project Charter

## Purpose

This document defines the identity, mission, scope, and long-term objectives of Learning OS.

It establishes the fundamental direction of the project and serves as the highest-level product document.

All future Specifications MUST remain consistent with this Charter.

---

# Mission

Learning OS exists to provide a deterministic, local-first learning runtime that enables users to organize, execute, and record structured learning journeys through portable Learning Graphs.

The project focuses on supporting self-directed learning rather than replacing it.

Learning OS assists users in understanding where they are, what they have completed, and what remains to be learned.

It does not attempt to become the learner.

---

# Vision

Learning should be:

- structured rather than fragmented;
- persistent rather than temporary;
- portable rather than platform-dependent;
- transparent rather than hidden;
- owned by the learner rather than by a service provider.

Learning OS aims to become an open runtime capable of executing any compliant Learning Graph regardless of subject or domain.

---

# Scope

Learning OS is responsible for:

- executing Learning Graphs;
- managing user progress;
- recording learning evidence;
- tracking learning history;
- visualizing learning structure;
- providing deterministic progression rules;
- supporting offline-first learning.

Learning OS is not responsible for:

- generating learning content;
- automatically evaluating knowledge;
- replacing teachers or mentors;
- providing online courses;
- recommending learning based on opaque algorithms;
- acting as an AI tutor.

---

# Core Concepts

Learning OS is built upon the following concepts.

## Learning Graph

Knowledge is represented as a structured graph.

The graph defines learning relationships but contains no user progress.

---

## Runtime

The Runtime executes Graphs.

It manages state, progression, persistence, and navigation.

The Runtime remains independent from any specific learning domain.

---

## User Progress

Progress belongs exclusively to the user.

User progress is stored independently from Graph packages.

Replacing or updating a Graph must not destroy user progress.

---

## Self-Evaluation

Learning completion is determined by the learner.

The Runtime records progress.

It does not judge mastery.

---

# Design Objectives

The project is guided by the following objectives.

## Local First

All core functionality must work without network connectivity.

---

## Deterministic

The same Graph and the same user state must always produce the same Runtime behavior.

---

## Portable

Learning Graphs should be transferable between different Runtime implementations.

---

## Extensible

New Graphs, Nodes, Tasks, and future extensions should be added without modifying the Runtime architecture.

---

## Transparent

Progression rules should be visible to the learner.

No hidden recommendation or scoring mechanisms should influence learning progression.

---

# Success Criteria

The project succeeds when:

- users can track long-term learning without platform lock-in;
- Graph packages can be shared independently of Runtime implementations;
- user progress remains portable;
- new learning domains can be supported without Runtime modification;
- contributors can extend the project through Specifications rather than rewriting the architecture.

---

# Non-Goals

The following are intentionally outside the scope of Version 1.

- Cloud synchronization
- Social networking
- Competitive ranking
- Automatic grading
- AI-generated learning plans
- Mandatory online services

These features may be explored independently in future versions without changing the core architecture.

---

# Specification Authority

This Charter governs all subsequent Specifications.

If a lower-level Specification conflicts with this document, this document takes precedence until an Architecture Decision Record (ADR) formally revises the Charter.

---

# Acceptance Criteria

This document is considered complete when:

- the project identity is clearly defined;
- project scope and boundaries are explicit;
- long-term objectives are documented;
- non-goals are clearly identified;
- future Specifications can reference this document without redefining project intent.

---

# Next Document

Continue reading:

**LOS-0101 — Vision**

---

# Agent Note

This document defines project intent.

Do not derive implementation details directly from this document.

Implementation behavior must always be defined by lower-level Specifications.