---
id: LOS-0500
title: First Runtime Implementation
status: Draft
version: 0.1.0
owner: Learning OS
last_updated: 2026-07-12

depends_on:
  - LOS-0305
  - LOS-0400
  - LOS-0401
  - LOS-0402
  - LOS-0403
  - LOS-0404
  - LOS-0405
  - LOS-0406
  - ADR-0001
  - ADR-0002

referenced_by:
  - future implementation documents

applicable_articles: []
---

# First Runtime Implementation

## Purpose

This document defines the scope, deliverables, and acceptance criteria for the first Learning OS Runtime prototype (Sprint 5).

This is the first code-producing Sprint. All prior Sprints produced only specifications.

The goal is to validate the core architecture with a minimal, testable, and deterministic Runtime.

---

# Sprint 5 Goal

Implement a minimal Runtime that executes the core Learning OS loop:

```
Load Graph Package
        ↓
Interpret Nodes and Edges
        ↓
Generate Available Learning State
        ↓
Accept User Progress Updates
        ↓
Persist User State
```

Target version: **v0.5.0-first-runtime**.

---

# MVP Scope

## Must Have

| Capability | Acceptance |
|------------|------------|
| Load a valid Graph Package (manifest.yaml + graph.yaml) | All Nodes and Edges correctly parsed into memory |
| Validate Graph structure | Reject: missing required fields, duplicate Node IDs, Edge references to unknown Nodes |
| Query Nodes | `list all`, `get by ID` |
| Initialize User State | All Nodes start at NOT_STARTED, bound to a Graph reference |
| Update Node status | `NOT_STARTED → IN_PROGRESS → COMPLETED → MASTERED` |
| Reject invalid status transitions | Skipping states is rejected with an error |
| Calculate completion statistics | `completed / total` |
| Resolve available Nodes | Source completed → prerequisite/dependency/progression target becomes available |
| Persist User State | Save to `data/user-state.json` as JSON |
| Restore User State | Load existing `data/user-state.json` on startup |
| Preserve progress across Graph reloads | Matching Node IDs retain progress |
| CLI interface | `los graph load/info`, `los node list/info/complete`, `los status` |
| Deterministic behavior | Same Graph + same State → identical outputs |
| Local-only execution | No network dependency |

## Must Not Have

- LLM or AI integration
- Automatic mastery assessment
- Graphical UI or skill tree visualization
- Cloud synchronization or online services
- User accounts or community platform
- Plugin system
- Extension Model implementation
- Edge condition evaluation
- Multi-file Graph Package layout (nodes/ + edges/ directories)
- Evidence storage beyond text references
- Gamification (XP, badges, achievements)

---

# Implementation Phases

Phases are ordered by dependency. Each phase is independently testable.

```
Phase 1: Package Skeleton
    └─ los package, pyproject.toml, __init__.py files

Phase 2: Graph Data Models
    └─ los/graph/models.py (Node, Edge dataclasses)

Phase 3: State Data Models
    └─ los/state/models.py (UserState, NodeState dataclasses)

Phase 4: Storage Layer
    └─ los/storage/adapter.py (JSON read/write)

Phase 5: Graph Loader
    └─ los/graph/loader.py (YAML parsing)
    └─ los/graph/validator.py (structure validation)

Phase 6: State Engine
    └─ los/state/engine.py (status machine, statistics)

Phase 7: Runtime Engine
    └─ los/engine/resolver.py (available node calculation)

Phase 8: CLI Interface
    └─ los/cli/main.py (argparse commands)

Phase 9: Entry Point
    └─ los/main.py (assembly and startup)
```

---

# Required Files

## Runtime Code

```
runtime/
├── pyproject.toml
└── los/
    ├── __init__.py
    ├── main.py
    ├── graph/
    │   ├── __init__.py
    │   ├── models.py
    │   ├── loader.py
    │   └── validator.py
    ├── state/
    │   ├── __init__.py
    │   ├── models.py
    │   └── engine.py
    ├── storage/
    │   ├── __init__.py
    │   └── adapter.py
    ├── engine/
    │   ├── __init__.py
    │   └── resolver.py
    └── cli/
        ├── __init__.py
        └── main.py
```

## Tests

```
tests/
├── test_graph_models.py
├── test_graph_loader.py
├── test_graph_validator.py
├── test_state_models.py
├── test_state_engine.py
├── test_storage_adapter.py
├── test_resolver.py
└── test_cli.py
```

## Example Data

```
graphs/
└── example-basics/
    ├── manifest.yaml
    └── graph.yaml
```

Total: 16 Python files, 1 pyproject.toml, 2 YAML data files.

---

# Dependency Rules

Source: [LOS-0401](file:///c:/Users/Kcirt/SAI%20Learning/LearningOS/spec/implementation/LOS-0401-project-structure.md#L330-L378)

```
interface
    ↓
engine
    ↓
graph / state
    ↓
storage
```

Forbidden dependencies:

- `graph/` MUST NOT import from `state/`
- `state/` MUST NOT import from `cli/`
- `graph/` and `state/` MUST NOT import from `engine/`
- `engine/` MAY import from both `graph/` and `state/`

---

# Testing Strategy

## Per-Phase Testing

Each phase includes corresponding tests. Tests are written alongside or immediately after implementation.

## Core Test Scenarios

### Load Graph

- Valid package loads successfully.
- Missing manifest.yaml produces clear error.
- Missing required field in manifest/graph produces clear error.
- Duplicate Node ID is rejected.
- Edge referencing unknown Node is rejected.
- Loading same package twice produces identical internal model.

### Update State

- All Nodes initialized to NOT_STARTED on first load.
- Valid transitions: NOT_STARTED → IN_PROGRESS → COMPLETED → MASTERED succeed.
- Invalid transitions (skipping states) are rejected.
- Completing a prerequisite makes dependent Nodes available.
- Completion statistics are correct.

### Persist State

- Write State to disk, read back, data matches.
- Graph reload preserves progress for Nodes with matching IDs.
- Nodes removed from Graph become orphaned (preserved in history).
- `schema_version` field is present in stored data.
- State references Node by ID, not by title.

## Test Command

```
pytest tests/
```

---

# CLI Commands Reference

Source: [LOS-0402](file:///c:/Users/Kcirt/SAI%20Learning/LearningOS/spec/implementation/LOS-0402-command-interface.md#L88-L412)

```
los graph load <package_path>
    Load a Graph Package from the given path.

los graph info
    Display current Graph name and version.

los node list
    List all Node IDs and titles, with availability status.

los node info <node_id>
    Display full Node details.

los node complete <node_id>
    Update Node status to COMPLETED.

los status
    Display completion statistics (completed / total).
```

---

# Definition of Done

Sprint 5 is complete when:

- [ ] Graph Package (manifest.yaml + graph.yaml) can be loaded and validated.
- [ ] All Nodes and Edges are queryable after loading.
- [ ] User State can be initialized, updated, and persisted.
- [ ] Status transitions follow the defined state machine.
- [ ] Available Nodes are correctly calculated from prerequisite Edges.
- [ ] All five CLI commands function correctly.
- [ ] All specified tests pass.
- [ ] No architecture violations exist (forbidden imports, domain knowledge leakage).
- [ ] Runtime operates entirely offline.

---

# Out of Sprint Scope

The following are explicitly deferred to future Sprints:

- Extension Model loading and discovery
- Edge condition evaluation (score thresholds, evidence requirements)
- Evidence file management beyond text references
- `los state export/import` commands
- `los config` command
- Configuration file support (config/settings.yaml)
- Multi-file Graph Package layout
- Graph Package version migration
- Multiple concurrent Graph packages
- Performance optimization
- Package distribution or sharing

---

# Acceptance Criteria

This document is complete when:

- Sprint 5 goal is unambiguously defined;
- MVP scope boundaries are explicit;
- implementation phases have clear dependency ordering;
- required files are enumerated;
- testing strategy covers the core loop;
- non-goals are documented;
- Definition of Done is measurable.

---

# Next Step

Begin Phase 1 implementation: Package Skeleton.

---

# Agent Note

This is the first implementation Sprint.

Rules:

1. Read LOS-0305 before implementing the Graph Loader.
2. Follow the phase order — do not skip phases.
3. Write tests alongside implementation.
4. Do not introduce architecture not defined in this document or ADRs.
5. Keep the Runtime generic — no domain-specific logic.
6. User progress belongs in `data/`, not in `graphs/`.
7. Node ID is the primary key everywhere.
