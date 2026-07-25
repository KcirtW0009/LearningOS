# ADR-0005: User State Migration and Continuity Preservation Contract

- Status: Accepted Candidate
- Date: 2026-07-13
- Decision Type: Architecture Contract

---

# Context

LearningOS requires Graph evolution without losing user-owned learning history.

As Graph Packages evolve:


Graph Version A

    ↓

Graph Version B


the Runtime may need to transform how existing user progress is interpreted.

However, user progress is not a property of a Graph Package.

It represents historical facts produced through user interaction.

Therefore, State Migration must answer:

- Who owns migration authority?
- Who defines migration meaning?
- What happens when migration fails?
- How is historical user progress preserved?

Without explicit boundaries, Graph evolution may incorrectly gain authority over user history.

---

# Decision

## 1. User State is a User-Owned Semantic Asset

User progress state MUST NOT be owned by:

- Graph Package;
- Runtime Graph Instance;
- Session;
- Migration Provider.

User State represents historical learning facts.

Therefore:


Graph

interprets State

Runtime

executes State

Migration

transforms interpretation

User

owns historical progress

---

## 2. Runtime owns Migration Authority

Migration execution authority belongs to Runtime.

Runtime is responsible for deciding:

- whether migration is allowed;
- which migration capability may execute;
- whether migration result is valid;
- whether the new Runtime context can become active.

Therefore:


Migration Capability

    provides transformation

            ↓

Runtime

    authorizes execution

Migration providers MUST NOT independently activate migrated state.

---

## 3. Migration Logic May Be Extended, but Execution MUST Be Controlled

The architecture allows migration capability extension.

Migration logic may be provided by:

- built-in Runtime components;
- trusted extension components;
- future migration frameworks.

However:


Migration Provider

    ≠

Migration Authority


The provider supplies transformation capability.

The Runtime retains execution authority.

---

## 4. Graph Package MUST NOT Directly Mutate User State

A Graph Package describes semantic structure.

It does not own user history.

Therefore:

Graph Package MUST NOT directly:

- modify user progress;
- rewrite historical records;
- establish new semantic ownership.

The relationship is:


Graph Evolution

    ↓

Migration Request

    ↓

Runtime-controlled State Transition


---

## 5. Migration MUST Preserve Historical Truth

Migration is not a destructive rewrite operation.

A successful migration creates a new interpretation of existing user state.

It does not erase historical facts.

Therefore:


Historical State

    +

Validated Continuity

    ↓

New State Interpretation


The original user history remains the authoritative record.

---

## 6. Migration MUST NOT Create Semantic Identity Continuity

Semantic continuity is defined by the Identity Layer.

Migration cannot establish:


Node A == Node B


through successful transformation.

A successful migration only proves:


State transformation is valid


It does not prove:


Semantic objects are identical


The relationship is:


Semantic Identity Layer

    defines continuity

            ↓

Migration

    preserves continuity

---

## 7. Migration Failure MUST Preserve Existing User State

A failed migration MUST NOT invalidate existing user-owned state.

The valid outcomes are:


Before Migration

    OR

After Successful Migration


Intermediate or partially migrated states MUST NOT become active Runtime state.

Therefore:


Migration Failure

    ↓

Reject New Runtime Context

    ↓

Preserve Existing State


---

## 8. Migration Activation MUST Be Atomic

From the Runtime perspective, migration is a transactional state transition.

The Runtime MUST NOT expose:


New Graph

    +

Partial Migration Result


as an active state.

Activation requires:


Migration Completed

    ↓

Validation Passed

    ↓

New Runtime Context Activated


---

# Consequences

## Positive Consequences

### User progress remains durable

Historical learning records survive:

- Graph upgrades;
- Runtime restart;
- Graph replacement;
- Migration failure.

---

### Responsibility boundaries remain clear

The architecture separates:


Identity Layer

defines semantic continuity

Graph Author

declares evolution intent

Migration Provider

provides transformation

Runtime

controls execution

User State

remains authoritative

---

### Supports long-term Graph evolution

Future migration mechanisms can evolve without changing ownership principles.

---

## Negative Consequences

### Migration requires explicit semantic information

Runtime cannot safely infer all migration relationships from structural changes.

---

### Migration becomes a controlled process

Automatic uncontrolled state transformation is intentionally restricted.

---

# Non-Goals

This ADR does NOT define:

- migration algorithm;
- migration step model;
- rollback mechanism;
- migration scripting format;
- migration storage format;
- conflict resolution strategy.

These belong to future implementation specifications.

---

# Relationship With Other ADRs

## ADR-0003: Node Identity and Semantic Continuity Contract

Defines:


What semantic continuity means.


Migration depends on identity continuity.

---

## ADR-0004: Graph Evolution, Versioning and Compatibility Resolution Contract

Defines:


How Graph evolution is evaluated.


Compatibility resolution determines whether migration is required.

---

## ADR-0005: User State Migration and Continuity Preservation Contract

Defines:


How user-owned state survives semantic evolution.


---

# Architectural Invariants

The following principles MUST remain stable:

1. User State is owned by the user, not by Graph or Runtime.

2. Runtime owns migration authority.

3. Migration capability does not imply migration authority.

4. Graph Packages MUST NOT directly mutate user state.

5. Migration preserves semantic continuity; it does not create identity.

6. Migration failure MUST NOT invalidate historical user progress.

7. Only validated migration results may become active Runtime state.

---

# Summary

LearningOS treats migration as a continuity-preserving interpretation transition rather than a destructive data transformation.

The architecture establishes:


Semantic Identity

    defines continuity

Graph Evolution

    introduces change

Compatibility Resolution

    determines migration requirement

Migration

    preserves user history

Runtime

    governs activation

The core principle is:

> Identity defines continuity. Migration preserves continuity. Runtime governs execution.

ADR-0005 完成后，三个核心 ADR 形成闭环：

ADR-0003
Node Identity
        |
        | defines "what remains the same"
        v

ADR-0004
Graph Evolution & Compatibility
        |
        | defines "how change is understood"
        v

ADR-0005
State Migration
        |
        | defines "how user history survives change"
        v

Runtime Specification