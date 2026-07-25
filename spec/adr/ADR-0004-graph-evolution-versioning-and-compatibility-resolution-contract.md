# ADR-004: Graph Evolution, Versioning and Compatibility Resolution Contract

- Status: Accepted Candidate
- Date: 2026-07-13
- Decision Type: Architecture Contract

---

## Context

LearningOS Runtime requires the ability to evolve Graph definitions while preserving user learning continuity.

A Graph Package may change over time due to:

- knowledge structure refinement;
- node addition or removal;
- semantic relationship changes;
- metadata or representation updates.

However, not all changes have the same architectural impact.

A fundamental distinction must be maintained:
Graph Package Change

    !=

Semantic Evolution

    !=

Runtime Compatibility

    !=

State Migration Requirement


Without this separation, version information may incorrectly become a substitute for semantic judgment, causing ambiguity in:

- identity continuity;
- compatibility evaluation;
- migration decisions;
- user state preservation.

Therefore, this ADR defines how Graph evolution, versioning, and compatibility decisions are interpreted.

---

# Decision

## 1. Version MUST NOT represent all types of change

A Graph Package version MUST NOT be interpreted as a complete description of semantic or runtime change.

Version information represents an evolution point of a Graph Package, but different types of change must remain conceptually separated.

The architecture recognizes three independent concerns:


Artifact Revision

    |

Semantic Evolution

    |

Runtime Compatibility


---

## 2. Artifact Revision and Semantic Evolution are independent concepts

A change in Graph representation does not necessarily imply semantic evolution.

Examples:

Representation-only change:


Documentation updated

Metadata changed

Formatting changed


does not necessarily affect semantic continuity.

Conversely, a small structural modification may introduce significant semantic change:


Node relationship changed

Prerequisite modified

Learning objective refined


Therefore:


Artifact Difference

cannot directly determine

Semantic Difference


---

## 3. Semantic Change MUST be explicitly declared

Runtime MUST NOT infer semantic meaning purely from structural comparison.

Graph diff operations can detect:

- node addition;
- node removal;
- edge changes;
- metadata changes.

However, they cannot reliably determine semantic intent.

For example:


Node A removed

Node B added


may represent:

- replacement;
- rename;
- refinement;
- split;
- merge.

Therefore:

Semantic evolution intent MUST be provided through explicit declaration.

---

## 4. Graph Author declares evolution intent

Graph Authors are responsible for declaring the intended semantic evolution.

The declaration represents:


Author Intent

    ↓

Semantic Change Description


The Graph Author provides semantic context that cannot be derived from representation alone.

However:

Graph Author is not the final authority for compatibility.

---

## 5. Runtime owns compatibility resolution authority

Runtime is responsible for evaluating whether a Graph evolution can safely coexist with existing user state.

Compatibility evaluation considers:


New Graph Evolution

    +

Existing User State Context

    ↓

Compatibility Resolution


Compatibility is therefore not an intrinsic property of a Graph version.

It is a relationship between:

- evolved Graph semantics;
- existing user state;
- available continuity information.

---

## 6. Compatibility resolution produces Runtime Action

Compatibility analysis MUST produce an explicit runtime decision.

The architecture recognizes the following conceptual outcomes:


ACCEPTED

MIGRATION_REQUIRED

REJECTED


These represent runtime actions rather than version categories.

Meaning:

### ACCEPTED

The new Graph context can safely operate without state transformation.

---

### MIGRATION_REQUIRED

Existing user state requires a validated migration before activation.

---

### REJECTED

The Runtime cannot establish a safe continuation of existing state.

---

## 7. Migration Requirement is not a Version Property

A version transition MUST NOT directly imply:


Version A

↓

Migration Required


Instead:


Graph Evolution

    +

Identity Continuity

    +

Existing State Context

    ↓

Migration Decision


Migration is determined by compatibility resolution.

---

# Consequences

## Positive Consequences

### Clear separation of responsibilities

The architecture establishes:


Graph Author

defines semantic intent

Runtime

validates compatibility

Migration Framework

transforms state

Identity Layer

defines continuity

---

### Prevents version overloading

Version numbers no longer become responsible for expressing:

- semantic meaning;
- compatibility guarantees;
- migration behavior.

---

### Supports long-term Graph evolution

Future Graph changes can introduce new evolution patterns without changing the fundamental versioning contract.

---

## Negative Consequences

### Additional metadata is required

Graph evolution requires explicit semantic change descriptions.

Automatic inference alone is insufficient.

---

### Compatibility evaluation becomes context-dependent

A Graph version may be:

compatible for a new user,

but require migration for an existing user.

---

# Non-Goals

This ADR does NOT define:

- version numbering scheme;
- SemVer adoption;
- manifest file format;
- change declaration syntax;
- migration algorithm;
- rollback mechanism.

These belong to future implementation specifications.

---

# Relationship With Other ADRs

## ADR-003: Node Identity and Semantic Continuity Contract

Provides:


What is considered the same semantic object?


Graph evolution depends on identity continuity.

---

## ADR-004: Graph Evolution, Versioning and Compatibility Resolution Contract

Provides:


How does the system understand semantic change?


---

## ADR-005: User State Migration and Continuity Preservation Contract

Provides:


How is user state preserved across accepted evolution?


---

# Architectural Invariants

The following principles MUST remain stable:

1. Version MUST NOT be treated as semantic authority.

2. Graph structural difference MUST NOT automatically imply semantic difference.

3. Semantic evolution intent MUST be explicitly declared.

4. Runtime MUST own compatibility resolution authority.

5. Migration requirement MUST be determined from compatibility analysis, not version labels.

6. Compatibility decisions MUST consider existing user state context.

---

# Summary

LearningOS treats Graph evolution as a semantic process rather than a file revision process.

The architecture separates:


Representation Change

    ↓

Semantic Evolution

    ↓

Compatibility Resolution

    ↓

Migration Requirement


This separation ensures that Graph evolution can occur without compromising identity continuity or user-owned learning history.