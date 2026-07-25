---
id: ADR-0001
title: CLI First Interface
status: Accepted
date: 2026-07-12
owner: Learning OS

related:
  - LOS-0402
  - LOS-0400
---

# ADR-0001: CLI First Interface

## Status

Accepted

---

# Context

Learning OS Runtime requires an external interaction interface.

Possible initial implementations include:

- Command Line Interface (CLI);
- Desktop Application;
- Web Application.

The first Runtime prototype focuses on validating the correctness of the core architecture, including:

- Graph loading;
- State management;
- Storage persistence.

Therefore, the initial interface should introduce minimal complexity.

---

# Decision

The first Learning OS Runtime will adopt a Command Line Interface (CLI) as the primary interaction interface.

The CLI will act as an adapter layer above Runtime Core.

Architecture:

```
User

 ↓

CLI Interface

 ↓

Runtime Core

 ↓

Graph / State / Storage
```

---

# Reasons

## Simplicity

CLI requires fewer dependencies and allows rapid prototype development.

---

## Testability

Commands can be easily tested automatically.

Example:

```
los status

los node list

los node complete <id>
```

---

## Architecture Validation

A CLI interface allows verification of whether Runtime Core is correctly separated from presentation.

---

# Alternatives Considered

## Desktop Application

Advantages:

- better user experience;
- suitable for RPG-style visualization.

Rejected for initial implementation because:

- higher development complexity;
- UI may hide Runtime architecture problems.

---

## Web Application

Advantages:

- easy distribution;
- modern interface.

Rejected for initial implementation because:

- requires additional frontend/backend architecture;
- introduces unnecessary deployment complexity.

---

# Consequences

## Positive Consequences

- Faster prototype development;
- Clear separation between Core and Interface;
- Easy automation testing;
- Future interfaces can reuse the same Runtime.

---

## Negative Consequences

- Initial user experience is limited;
- No graphical skill tree visualization.

These limitations are acceptable for the prototype stage.

---

# Future Considerations

Future interfaces MAY include:

- Desktop UI;
- Web UI;
- Mobile UI;
- AI Agent interface.

These interfaces SHOULD reuse the existing Runtime Core.

---

# Principle

The interface is replaceable.

The Runtime Core is the product.