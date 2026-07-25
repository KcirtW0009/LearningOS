# ADR-002: Node Identity and Semantic Continuity Contract

- Status: Accepted Candidate
- Date: 2026-07-13
- Decision Type: Architecture Contract
- Related:
  - AD-007 Semantic Identity Foundation
  - AD-003 Graph Evolution, Versioning and Compatibility
  - AD-004 User State Migration and Continuity Preservation

---

# 1. Context

LearningOS represents learning structures as semantic graphs.

During the lifecycle of a learning graph, the same semantic object may appear across different representations, graph versions, runtime instances, and storage contexts.

Examples:

- Graph package updates
- Runtime graph replacement
- Graph evolution
- State migration

require the system to determine whether an object before and after change represents the same semantic entity.

Without an explicit identity model, Runtime components may incorrectly infer continuity from:

- representation similarity
- position in graph structure
- display names
- runtime references
- storage identifiers

These approaches cannot guarantee semantic continuity.

Therefore, LearningOS requires an explicit Identity Contract defining how semantic objects maintain continuity across their lifetime.

---

# 2. Decision

LearningOS adopts the following principle:

> Identity represents semantic continuity, not representation.

A Node Identity identifies a semantic object whose meaning remains stable across different representations and runtime contexts.

Identity is independent from:

- File format
- Serialization format
- Display name
- Runtime instance
- Storage location

---

# 3. Architecture Contracts

## Contract 1 — Identity MUST be Explicit

Runtime MUST NOT create, infer, or guess semantic identity.

Identity MUST be declared by the semantic authoring layer.

Runtime MAY:

- read identity
- validate identity
- store identity references
- propagate identity references

Runtime MUST NOT:

- generate missing identity
- infer identity from structure
- derive identity from presentation information

---

## Contract 2 — Identity Exists to Preserve Semantic Continuity

Identity exists because semantic objects may evolve over time.

The purpose of Identity is:

> Preserve the ability to recognize the same semantic object across evolution.

Identity continuity is a semantic judgment.

It is not determined by:

- runtime observation
- structural similarity
- version numbers
- migration success

---

## Contract 3 — Runtime Identity Resolution MUST be Deterministic

Runtime operations involving identity resolution MUST produce deterministic results.

Given the same semantic context and identity declarations, Runtime MUST reach the same identity interpretation.

Identity resolution MUST NOT depend on:

- execution order
- runtime state
- accidental graph structure

---

## Contract 4 — Identity MUST Exist Within a Defined Scope

Every Identity MUST belong to an explicit scope.

The scope defines where the identity relationship is meaningful.

This ADR does not define:

- Workspace scope
- Registry scope
- Cross-graph ownership
- Global identity namespace

Those topics are deferred.

---

# 4. Identity Lifecycle Model

Identity follows the semantic lifecycle:
Semantic Object

    |
    v

Identity Declaration

    |
    v

Runtime Validation

    |
    v

Semantic Reference


Runtime validation establishes whether an identity declaration can participate in the Runtime model.

Validation does not create identity.

---

# 5. Relationship with Other Architecture Decisions

## AD-003 — Graph Evolution and Compatibility

AD-002 provides the foundation for understanding change.

Relationship:


Identity Continuity

    ↓

Semantic Change Analysis

    ↓

Compatibility Resolution


Version changes alone cannot determine semantic continuity.

---

## AD-004 — State Migration

Migration relies on identity continuity.

Relationship:


Identity Continuity

    ↓

Migration Relationship

    ↓

State Interpretation Update


Migration MUST NOT create semantic identity.

---

# 6. Consequences

## Positive Consequences

### Stable Semantic Reference

Components can safely reference semantic objects across:

- graph evolution
- runtime replacement
- state migration

---

### Clear Responsibility Boundary

Responsibilities are separated:

| Responsibility | Owner |
|---|---|
| Identity declaration | Semantic authoring layer |
| Identity validation | Runtime |
| Identity consumption | Runtime components |
| Identity continuity judgment | Semantic layer |

---

### Prevent Representation Leakage

Future implementations may use:

- YAML
- JSON
- Database
- Registry
- Protocol formats

without changing the Identity Contract.

---

## Negative Consequences

Identity management introduces additional explicit metadata requirements.

Authors must define semantic identity rather than relying on automatic inference.

---

# 7. Deferred Topics

The following topics are intentionally excluded:

## Identity Ownership

Who owns identity across:

- Workspace
- Registry
- Community graph sharing

is deferred.

---

## Identity Storage Model

How identities are persisted is a Specification concern.

---

## Identity Encoding

Representation formats are not architectural decisions.

---

# 8. Observations

## AO-002 — Identity Ownership

Identity ownership is an important future architectural topic but requires additional context:

- Workspace model
- Registry model
- Cross-graph references
- Semantic object model

Therefore it remains an Observation rather than an Architecture Decision.

---

# 9. Summary

LearningOS adopts explicit semantic identity as the foundation for graph evolution.

The core principle is:

> Identity defines what remains the same. Representation defines only how it is expressed.

Identity continuity is established by semantic rules and consumed by Runtime systems to support version evolution, compatibility analysis, and state migration.