# RS-002 — Runtime Graph Lifecycle State Machine

## Status

Frozen

---

# 1. Purpose

This specification defines the lifecycle model and transition authority of Runtime Graph Instance.

---

# 2. Lifecycle Principle

Lifecycle states represent stable runtime phases.

Lifecycle states do not represent every possible runtime condition.

---

# 3. Lifecycle State Model

The Runtime Graph Instance lifecycle is:
CREATED

|

v

VALIDATED

|

v

ACTIVATED

|

v

ACTIVE

|

v

RETIRED


---

# 4. Lifecycle Authority

## Contract 1 — Transition Ownership

Runtime lifecycle transitions are owned by Runtime Authority.

External components MAY request transitions.

External components MUST NOT directly mutate lifecycle state.

---

# 5. Failure Separation

## Contract 2 — Failure Is Not Lifecycle State

Failure conditions MUST be represented as:

- runtime events;
- transition outcomes;
- operational conditions.

Failure conditions MUST NOT automatically create lifecycle states.

Example:

Invalid:


ACTIVE

↓

FAILED


Correct:


ACTIVE

↓

Runtime Event

↓

Recovery Decision


---

# 6. Retirement Finality

## Contract 3 — RETIRED Is Terminal

A Runtime Graph Instance entering RETIRED state MUST NOT return to ACTIVE.

Reactivation requires creation of a new Runtime Graph Instance identity.

---

# 7. Lifecycle Boundary

Lifecycle controls:

- runtime availability;
- execution eligibility;
- operational phase.

Lifecycle does not control:

- semantic identity;
- user state ownership;
- session lifetime.

---

# 8. Consistency Requirements

The following MUST hold:


Runtime Instance Identity

    remains stable

throughout

Lifecycle History


Lifecycle transition MUST NOT:

- change Semantic Graph Binding;
- transfer State Ownership;
- create new Session Identity.

---

# 9. Deferred Topics

Outside this specification:

- Recovery workflow
- Failure handling model
- Operational pause
- Runtime restart procedure