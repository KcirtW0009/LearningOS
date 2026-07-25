# Architecture Board Freeze Document

# RS-005 — Runtime Resolver Interface

Status:

```text
APPROVED
```

---

# 1. Purpose

RS-005 defines the responsibility boundary and interaction contract of Runtime Resolver.

The objective is to ensure that Runtime Resolver performs Runtime Context resolution without becoming:

* Semantic Authority
* Lifecycle Authority
* Runtime Selection Authority
* State Authority

---

# 2. Final Contract Set

---

## Contract 1 — Resolver Responsibility Boundary

### Decision

Runtime Resolver is responsible for resolving suitable Runtime Execution Contexts.

It does not own:

* Semantic Identity
* Runtime Lifecycle
* User State
* Migration Authority

Relationship:

```text
Request Context

        ↓

Runtime Resolver

        ↓

Runtime Context Candidates
```

---

## Contract 2 — Resolution Input Context

### Decision

Runtime Resolver resolves Runtime Context based on runtime-relevant context information.

Allowed inputs include:

* Session Context
* Semantic Context Reference
* Runtime Constraints
* Availability Information

Resolver does not define:

* Semantic equivalence
* Graph meaning
* State ownership

---

## Contract 3 — Resolution Result Separation

### Decision

Runtime Resolver may return one or more valid Runtime Context candidates.

Final Runtime selection is performed by Runtime Authority or an authorized selection component.

Flow:

```text
Resolution Request

        ↓

Runtime Resolver

        ↓

Runtime Candidates

        ↓

Runtime Authority Selection

        ↓

Selected Runtime Instance
```

---

## Contract 4 — Resolution Failure Boundary

### Decision

When no valid Runtime Context exists, Resolver reports resolution failure.

Resolver does not:

* create Runtime Instance
* activate Runtime
* change lifecycle state
* migrate state

---

## Contract 5 — Lifecycle Information Usage

### Decision

Runtime Resolver may consume lifecycle information for eligibility evaluation.

Lifecycle transition authority remains exclusively owned by Runtime Authority.

Allowed:

```text
ACTIVE Runtime

        ↓

Eligible Candidate
```

Not allowed:

```text
Resolver

        ↓

Activate Runtime
```

---

# 3. Boundary Freeze

## Runtime Resolver owns:

* Runtime Context discovery
* Candidate filtering
* Availability evaluation

---

## Runtime Resolver does not own:

* Runtime creation
* Runtime identity generation
* Lifecycle transition
* Final runtime selection policy
* State interpretation

---

# 4. Cross-Spec Consistency Check

## RS-001 Runtime Graph Instance Model

Consistent:

```text
Runtime Identity

exists before

Resolution
```

Resolver references existing Runtime Instances.

---

## RS-002 Runtime Lifecycle State Machine

Consistent:

```text
Resolver reads lifecycle state

but does not control lifecycle
```

---

## RS-003 Session Binding Model

Consistent:

```text
Resolver resolves context

Runtime Authority establishes binding
```

---

## RS-004 State Access Contract

Consistent:

```text
State does not become Runtime Resolution Authority
```

---

## RS-006 Runtime Authority Model

Consistent:

```text
Resolver

        provides candidates

Runtime Authority

        performs final selection
```

---

# 5. Freeze Decision

Architecture Board Decision:

```text
RS-005 — Runtime Resolver Interface

APPROVED
```

Final Principle:

> Runtime Resolver provides eligible Runtime Context candidates. It performs context resolution only and does not own Runtime lifecycle, semantic meaning, state authority, or final runtime decisions.
