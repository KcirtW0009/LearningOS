---
id: LOS-0600
title: Sprint 6 — Stabilization & Foundation
status: Draft
version: 0.1.0
owner: Learning OS
last_updated: 2026-07-12

depends_on:
  - LOS-0500
  - LOS-0406
  - ADR-0001
  - ADR-0002

referenced_by:
  - future implementation documents

applicable_articles: []
---

# Sprint 6 — Stabilization & Foundation

## Purpose

This document defines the scope, deliverables, and acceptance criteria for Sprint 6.

Sprint 5 (v0.5.0-first-runtime) delivered the MVP core loop: load graph → query nodes → update state → persist. Sprint 6 is a **stabilization sprint** focused on closing governance gaps, resolving deferred hygiene items, and hardening the codebase for the next feature Sprint.

Sprint 6 is **not** a feature Sprint. No new runtime capabilities are added. The goal is to raise quality to a level that supports confident iteration in Sprint 7+.

---

# Sprint 6 Goal

Close the gap between prototype-quality code and a maintainable foundation by addressing deferred governance tasks, filling test coverage holes, and establishing conventions that the entire codebase follows.

```
Closure Audit (read-only)
        ↓
Governance Tasks (G4, G6, G7, G10)
        ↓
Technical Debt Resolution (TD-002, TD-003)
        ↓
Validation
```

Target version: **v0.6.0-stabilization**.

---

# Scope

## In Scope

| Task ID | Description | Source |
|---------|-------------|--------|
| G4 | Resolve `_utc_now_iso` duplication | Governance deferred / TD-003 |
| G6 | Recreate persistent tests for Phases 2–5 | Governance deferred / TD-002 |
| G7 | Rename test files from phase-convention to module-convention | Governance deferred |
| G10 | Introduce exception hierarchy | Governance deferred |

## Explicitly Out of Scope

- New runtime features (deferred to Sprint 7)
- `graph_path` extraction from UserState (TD-001, target v0.7+)
- Extension Model loading
- Edge condition evaluation
- `los state export/import`, `los config` commands
- Multi-file Graph Package layout
- Configuration file support
- Performance optimization
- Package distribution or sharing

---

# Task Breakdown

## G4 — Resolve `_utc_now_iso` duplication

**Current state**: The function `_utc_now_iso()` is defined identically in two files:

- `runtime/los/state/models.py` (line 171)
- `runtime/los/state/engine.py` (line 192)

A third variant exists inline in `runtime/los/storage/adapter.py` (line 177-179) using `datetime.now(timezone.utc).isoformat()` directly rather than a named helper.

**Problem**: Duplicated utility code violates DRY. The storage layer's inline variant is the least maintainable form.

**Constraint**: `storage/` cannot import from `state/` (dependency direction rule). The utility must live in a location accessible to all layers without creating circular imports or architectural violations.

**Proposed solution**: Create `runtime/los/common.py` at the package root as a zero-dependency utility module. Move `_utc_now_iso` there. All three consumers import from `los.common`.

**Proposed module**:

```python
# runtime/los/common.py
"""Shared utilities with zero internal dependencies.

This module MUST NOT import from any other los sub-package.
It exists solely to hold functions used by multiple layers
without violating dependency direction rules.
"""

from datetime import datetime, timezone


def utc_now_iso() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()
```

**Affected files**:

| File | Change |
|------|--------|
| `runtime/los/common.py` | **NEW** — single-source utility |
| `runtime/los/state/models.py` | Replace local `_utc_now_iso` with `from los.common import utc_now_iso` |
| `runtime/los/state/engine.py` | Replace local `_utc_now_iso` with `from los.common import utc_now_iso` |
| `runtime/los/storage/adapter.py` | Replace inline `datetime.now(timezone.utc).isoformat()` with `from los.common import utc_now_iso` |

**Acceptance criteria**:
- `_utc_now_iso` exists exactly once in the codebase
- All three consumers import from the same source
- No dependency direction violation (common.py imports nothing from los)
- All existing tests pass

---

## G6 — Recreate Tests for Phases 2–5

**Current state**: Tests exist only for Phase 6 (`test_phase6_engine.py`), Phase 7 (`test_phase7_resolver.py`), and Phase 8 (`test_phase8_cli.py`). Phases 2–5 were tested inline during implementation but tests were never saved as persistent files — this is documented as TD-002.

**Missing test files** (per LOS-0500 required test list):

| Phase | Missing test file | Target module |
|-------|-------------------|---------------|
| 2 | `test_graph_models.py` | `los/graph/models.py` — Node, Edge dataclasses |
| 3 | `test_state_models.py` | `los/state/models.py` — UserState, NodeState, HistoryEntry |
| 4 | `test_storage_adapter.py` | `los/storage/adapter.py` — save/load round-trip |
| 5 | `test_graph_loader.py` + `test_graph_validator.py` | `los/graph/loader.py` + `los/graph/validator.py` |

**Note on naming**: Per G7, the test files will be created with **module-convention names** (`test_graph_models.py`, `test_state_models.py`, etc.) rather than phase-convention names. Existing Phase 6–8 tests will be renamed in G7 to match.

**Coverage requirements** (per LOS-0500 test scenarios):

### test_graph_models.py
- Node: construction with valid fields, rejection of empty id/title/description
- Edge: construction with valid fields, rejection of empty source/target/relation
- Edge type enum validation
- Node and Edge immutability (frozen dataclass behavior)

### test_state_models.py
- NodeState: default status = NOT_STARTED, default score = 0
- NodeState: rejection of empty node_id, negative score
- NodeState: `is_completed` property for COMPLETED and MASTERED
- NodeState: `updated_at` auto-populated on creation
- UserState: defaults (user_id, empty graph_id, empty node_states)
- UserState: `created_at` and `updated_at` auto-populated
- UserState: `ensure_node_state` creates entry if absent
- UserState: `completed_count` and `total_count` properties
- HistoryEntry: construction, rejection of empty required fields
- HistoryEntry: frozen (immutable) behavior

### test_storage_adapter.py
- Save then load: data round-trips correctly
- Load of non-existent file returns fresh UserState
- `schema_version` field preserved
- Node states serialized and deserialized correctly
- History entries survive round-trip
- Orphaned node_ids (not in current graph) are preserved
- Evidence list serialization

### test_graph_loader.py
- Valid package (example-basics) loads successfully
- Missing manifest.yaml produces clear error
- Missing graph.yaml produces clear error
- Missing required Node fields produce clear errors
- Malformed YAML produces clear error
- Empty YAML file is rejected

### test_graph_validator.py
- Duplicate Node ID is rejected
- Edge referencing unknown source Node is rejected
- Edge referencing unknown target Node is rejected
- Valid graph passes validation without errors

**Validator fixture strategy**: The `example-basics/` package is a valid graph — it cannot provide invalid-graph scenarios (duplicate IDs, broken Edge references). Invalid test cases must be constructed programmatically. The loader exposes `validate_graph_structure(nodes, edges)` which accepts plain lists of dicts. Invalid graphs for validator testing should be constructed as inline dict fixtures, for example:

```python
# Duplicate Node ID
nodes = [
    {"id": "dup", "title": "A", "description": "First"},
    {"id": "dup", "title": "B", "description": "Second"},
]
edges = []
# → expect GraphValidationError
```

```python
# Edge references unknown Node
nodes = [{"id": "a", "title": "A", "description": "Desc"}]
edges = [{"from": "a", "to": "no-such", "relation": "prerequisite"}]
# → expect GraphValidationError
```

**Acceptance criteria**:
- All 5 missing test files exist under `tests/`
- `pytest tests/` passes with all tests (old + new)
- Each test file covers the scenarios listed above
- Tests use the `graphs/example-basics/` package as test fixture where applicable

---

## G7 — Rename Test Files to Module Convention

**Current state**: Test files use phase-based naming:

```
tests/
├── test_phase6_engine.py
├── test_phase7_resolver.py
└── test_phase8_cli.py
```

**Problem**: Phase numbers are Sprint-5-specific artifacts. As the project evolves, phase numbers become meaningless. Module-based names directly communicate what is being tested and survive refactoring.

**Target state**:

```
tests/
├── test_graph_models.py        (was: new in G6)
├── test_state_models.py        (was: new in G6)
├── test_storage_adapter.py     (was: new in G6)
├── test_graph_loader.py        (was: new in G6)
├── test_graph_validator.py     (was: new in G6)
├── test_state_engine.py        (was: test_phase6_engine.py)
├── test_resolver.py            (was: test_phase7_resolver.py)
└── test_cli.py                 (was: test_phase8_cli.py)
```

**Affected files**:

| Old name | New name |
|----------|----------|
| `test_phase6_engine.py` | `test_state_engine.py` |
| `test_phase7_resolver.py` | `test_resolver.py` |
| `test_phase8_cli.py` | `test_cli.py` |

**Execution order**: G7 runs **after** G6, so G6 creates new files with target names directly and G7 only renames the 3 existing files.

**Acceptance criteria**:
- No `test_phase*.py` files remain under `tests/`
- All test files follow `test_<module>.py` convention
- `pytest tests/` passes with renamed files
- Imports within test files (e.g., `from tests.utils import ...`) remain functional

---

## G10 — Introduce Exception Hierarchy

**Current state**: All error conditions use built-in exceptions:

- `ValueError` — used for validation failures, state transition errors, missing nodes, malformed data (30 occurrences across 6 files)
- `FileNotFoundError` — used for missing package paths (3 occurrences in `loader.py`)

**Problem**: Callers cannot distinguish between a "node not found" error and a "malformed YAML" error without string-matching on error messages. This is fragile and untestable. A structured exception hierarchy allows callers (especially the CLI) to handle error categories cleanly.

**Proposed hierarchy**:

```
Exception
 └── LOSError                    (base for all LearningOS errors)
      ├── GraphError             (graph loading / validation failures)
      │    ├── GraphNotFoundError
      │    ├── GraphParseError
      │    └── GraphValidationError
      ├── StateError             (state transition / node lookup failures)
      │    ├── NodeNotFoundError
      │    ├── InvalidStateTransitionError
      │    └── NodeAlreadyCompletedError
      └── StorageError           (persistence failures)
           └── SchemaVersionError
```

**Proposed module**: `runtime/los/exceptions.py`

```python
# runtime/los/exceptions.py
"""LearningOS exception hierarchy.

All LOS-specific errors inherit from LOSError.
Callers (CLI, future API) can catch LOSError for any LOS failure
or catch specific subclasses for targeted handling.
"""


class LOSError(Exception):
    """Base exception for all LearningOS errors."""
    pass


# ── Graph errors ───────────────────────────────────────────────────────

class GraphError(LOSError):
    """Base for graph loading and validation failures."""
    pass


class GraphNotFoundError(GraphError):
    """A required file or package path does not exist."""
    pass


class GraphParseError(GraphError):
    """Graph data is malformed (bad YAML, missing required fields)."""
    pass


class GraphValidationError(GraphError):
    """Graph structure is invalid (duplicate IDs, broken references)."""
    pass


# ── State errors ───────────────────────────────────────────────────────

class StateError(LOSError):
    """Base for state transition and node lookup failures."""
    pass


class NodeNotFoundError(StateError):
    """Requested node_id is not tracked in UserState."""
    pass


class InvalidStateTransitionError(StateError):
    """Attempted status transition violates the state machine."""
    pass


class NodeAlreadyCompletedError(StateError):
    """Attempted to complete a node that is already COMPLETED or MASTERED."""
    pass


# ── Storage errors ─────────────────────────────────────────────────────

class StorageError(LOSError):
    """Base for persistence failures."""
    pass


class SchemaVersionError(StorageError):
    """Stored data has an incompatible or missing schema_version."""
    pass
```

**Boundary rule — where custom exceptions apply**: The `LOSError` hierarchy is reserved for **runtime flow exceptions** only — errors that callers or users can meaningfully catch and distinguish at runtime. This includes graph loading, resolver/runtime operations, storage persistence, and CLI user-facing errors.

Dataclass `__post_init__` validation in `graph/models.py` and `state/models.py` (empty fields, negative scores, empty HistoryEntry fields) represents programmer-facing contract violations — internal invariants, not runtime conditions. These **keep `ValueError`** and are NOT migrated to custom exceptions.

**Migration map** (current → new):

| Current exception | Location | New exception |
|-------------------|----------|---------------|
| `FileNotFoundError` | `loader.py:100,106,110` | `GraphNotFoundError` |
| `ValueError` (empty YAML) | `loader.py:155` | `GraphParseError` |
| `ValueError` (bad YAML structure) | `loader.py:163,171,176,181,200,205,209,211,214,220` | `GraphParseError` |
| `ValueError` (validation errors) | `loader.py:130,135` | `GraphValidationError` |
| `ValueError` (complete_node) | `state/engine.py:64` | `NodeAlreadyCompletedError` |
| `ValueError` (start_node) | `state/engine.py:123` | `InvalidStateTransitionError` |
| `ValueError` (get_node_status) | `state/engine.py:178` | `NodeNotFoundError` |
| `ValueError` (_require_node_state) | `state/engine.py:188` | `NodeNotFoundError` |
| `ValueError` (schema_version) | `storage/adapter.py:128` | `SchemaVersionError` |

**Not migrated** (keep `ValueError` — internal invariants):

| Location | Reason |
|----------|--------|
| `graph/models.py:65,67,69` | Node.id/title/description empty — programmer error |
| `graph/models.py:103,105,107` | Edge.source/target/relation empty — programmer error |
| `state/models.py:62` | HistoryEntry required field empty — programmer error |
| `state/models.py:91,93` | NodeState empty node_id / negative score — programmer error |

**Acceptance criteria**:
- `runtime/los/exceptions.py` exists with the hierarchy defined above
- All `FileNotFoundError` in `loader.py` replaced with `GraphNotFoundError`
- All `ValueError` in `loader.py` replaced with appropriate `GraphParseError` or `GraphValidationError`
- All `ValueError` in `state/engine.py` replaced with appropriate `StateError` subclasses
- `ValueError` in `storage/adapter.py` line 128 replaced with `SchemaVersionError`
- CLI error handling (`los/cli/main.py`) updated to catch `LOSError` and display user-friendly messages
- Existing tests updated to expect new exception types
- New tests for exception hierarchy (verify isinstance relationships)
- All `LOSError` subclasses inherit from `LOSError`
- `pytest tests/` passes

---

# Implementation Phases

Phases are ordered by dependency. Each phase is independently testable.

```
Phase 10-1: G4 — Resolve _utc_now_iso duplication
    ├── NEW: runtime/los/common.py
    └── EDIT: state/models.py, state/engine.py, storage/adapter.py

Phase 10-2: G10 — Introduce exception hierarchy
    ├── NEW: runtime/los/exceptions.py
    ├── EDIT: graph/loader.py
    ├── EDIT: state/engine.py
    ├── EDIT: storage/adapter.py, cli/main.py
    └── EDIT: existing tests (update expected exceptions)

Phase 10-3: G6 — Recreate tests for Phases 2–5
    ├── NEW: tests/test_graph_models.py
    ├── NEW: tests/test_state_models.py
    ├── NEW: tests/test_storage_adapter.py
    ├── NEW: tests/test_graph_loader.py
    └── NEW: tests/test_graph_validator.py

Phase 10-4: G7 — Rename test files
    ├── RENAME: test_phase6_engine.py → test_state_engine.py
    ├── RENAME: test_phase7_resolver.py → test_resolver.py
    └── RENAME: test_phase8_cli.py → test_cli.py
```

---

# Required File Changes Summary

## New files (7)

```
runtime/los/common.py          # G4
runtime/los/exceptions.py      # G10
tests/test_graph_models.py     # G6
tests/test_state_models.py     # G6
tests/test_storage_adapter.py  # G6
tests/test_graph_loader.py     # G6
tests/test_graph_validator.py  # G6
```

## Modified files (8)

```
runtime/los/state/models.py    # G4
runtime/los/state/engine.py    # G4, G10
runtime/los/storage/adapter.py # G4, G10
runtime/los/graph/loader.py    # G10
runtime/los/cli/main.py        # G10
tests/test_phase6_engine.py    # G10 (exception types) → then G7 (rename)
tests/test_phase7_resolver.py  # G10 (exception types) → then G7 (rename)
tests/test_phase8_cli.py       # G10 (exception types) → then G7 (rename)
```

## Renamed files (3)

```
tests/test_phase6_engine.py  → tests/test_state_engine.py   # G7
tests/test_phase7_resolver.py → tests/test_resolver.py       # G7
tests/test_phase8_cli.py     → tests/test_cli.py             # G7
```

---

# Dependency Rules

Existing dependency direction remains enforced:

```
interface (cli)
    ↓
engine (resolver)
    ↓
graph / state
    ↓
storage
```

New modules `common.py` and `exceptions.py` sit at the package root with **zero internal dependencies** — they import nothing from `los.*`. This makes them safe to import from any layer.

```
los.common        ← importable by any layer
los.exceptions    ← importable by any layer
```

---

# Testing Strategy

## Existing tests

All existing tests must continue to pass after each phase. Exception type changes in G10 will require updating `pytest.raises(ValueError)` to the appropriate new type.

## New tests (G6)

Each new test file must:
- Import from the module it tests
- Cover the scenarios listed in the task breakdown
- Use `graphs/example-basics/` as fixture where applicable
- Follow the patterns established by existing tests

## Full suite

```
pytest tests/ -v
```

All tests must pass before Sprint 6 is declared complete.

---

# Definition of Done

Sprint 6 is complete when:

- [ ] `_utc_now_iso` exists in exactly one location (`los/common.py`) and all consumers import it
- [ ] Exception hierarchy exists in `los/exceptions.py` and all error-raising code uses it
- [ ] CLI displays user-friendly error messages for `LOSError` subclasses
- [ ] Missing Phase 2–5 tests exist and pass (5 new test files)
- [ ] No `test_phase*.py` files remain; all tests follow `test_<module>.py` convention
- [ ] `pytest tests/` passes with zero failures
- [ ] No architecture violations (dependency direction, domain knowledge leakage)
- [ ] Technical debt register updated: TD-002 resolved, TD-003 resolved

---

# Out of Sprint Scope

The following remain explicitly deferred:

- `graph_path` extraction from UserState (TD-001, target v0.7+)
- Extension Model loading and discovery
- Edge condition evaluation (score thresholds, evidence requirements)
- Evidence file management beyond text references
- `los state export/import` commands
- `los config` command
- Configuration file support (`config/settings.yaml`)
- Multi-file Graph Package layout
- Graph Package version migration
- Multiple concurrent Graph packages
- Performance optimization
- Package distribution or sharing

---

# Acceptance Criteria

This document is complete when:

- Sprint 6 goal is unambiguously defined as a stabilization sprint
- All four governance tasks (G4, G6, G7, G10) have clear scope, affected files, and acceptance criteria
- Implementation phases have correct dependency ordering
- Required files are enumerated (new, modified, renamed)
- Testing strategy covers both existing and new tests
- Non-goals are documented (no feature work)
- Definition of Done is measurable

---

# Agent Note

This is a stabilization Sprint. The rules are:

1. **Read-only until Host authorization.** This document is a plan — no implementation begins without explicit Host approval.
2. **No feature work.** Resist the temptation to improve or refactor beyond the defined task scope.
3. **G4 before G10 (convention, not requirement).** Both `common.py` and `exceptions.py` are independent root-level modules — neither imports the other. G4 is placed first to establish the root-module pattern before the larger G10 migration, but the two could be implemented in either order or in parallel.
4. **G6 before G7.** New tests created in G6 already use target names; G7 only renames the 3 legacy files.
5. **All tests must pass at every phase boundary.** Do not accumulate failures across phases.
6. **Update technical-debt.md** after resolving TD-002 and TD-003.

---

# Next Step

Await Host authorization to begin Phase 10-1 (G4: `_utc_now_iso` consolidation).

---

# Governance Reference

This plan incorporates the governance lessons from Sprint 6A Closure Audit:

1. Completed ≠ commit authorized — all phases require explicit Host approval
2. No git write without explicit Host approval
3. Only explicitly approved task IDs (G4, G6, G7, G10) may be implemented
4. Narrative "additional tasks" are recommendations only
5. Audit phase is read-only

The four task IDs listed here are drawn directly from the deferred tasks register and the technical debt register. No additional tasks have been introduced.
