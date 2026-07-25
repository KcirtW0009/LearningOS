# Technical Debt Register

Sprint 5 (v0.5.0-first-runtime) — documented architectural shortcuts and
their planned resolution paths.

---

## TD-001 — `graph_path` stored in UserState

**Status**: Acknowledged (MVP shortcut)

**Location**:
  - `runtime/los/state/models.py` — `UserState.graph_path` field
  - `runtime/los/cli/main.py` — `_ensure_loaded()` reads it for session recovery

**Why it exists**:
  The CLI runs as independent processes. Without `graph_path`, commands like
  `los status` or `los node list` would require the user to re-run
  `los graph load <path>` in every new terminal session. `graph_path`
  allows the CLI to automatically reload the last-used Graph Package from
  the persisted state file.

**Why it is technical debt**:
  `graph_path` is runtime/session metadata, not learning state. A filesystem
  path is machine-specific and non-portable. UserState should describe
  *what the user has learned*, not *where the graph is installed*.

  Mixing session metadata into UserState violates the principle that
  "User State belongs to the user" (LOS-0201) and makes the state file
  non-portable between machines.

**Migration target (v0.7+)**:
  Move `graph_path` (and any future session-level metadata) into a dedicated
  session metadata file (`data/session.json`), separate from
  `data/user-state.json`.

  Proposed session model:
  ```json
  {
    "last_graph_path": "graphs/example-basics",
    "last_used_at": "2026-07-12T10:00:00+00:00"
  }
  ```

  `_ensure_loaded()` would read `session.json` for the graph path,
  then `user-state.json` for learning progress. UserState would contain
  only `graph_id` and `graph_version` for reference.

**Resolution Sprint**: v0.7+ (requires session metadata design)

---

## TD-002 — Phase 2-5 tests not persisted

**Status**: Acknowledged

**Location**: Phases 2-5 implementation reports

**Why it exists**:
  Tests for Graph Models, State Models, Storage Adapter, Graph Loader, and
  Graph Validator were run inline during implementation but were never saved
  as standalone files under `tests/`.

**Resolution Sprint**: Sprint 6B (or next development Sprint)

---

## TD-003 — Duplicated `_utc_now_iso()` between state and storage

**Status**: Acknowledged

**Location**:
  - `runtime/los/state/models.py`
  - `runtime/los/state/engine.py`
  - `runtime/los/storage/adapter.py`

**Why it exists**:
  The storage layer cannot import from the state layer for a utility function
  without violating the dependency direction (`storage/` is the bottom layer).
  The function is only 2 lines — the cost of duplication is lower than the
  cost of architectural violation.

**Resolution**: Keep as-is unless a `common.py` utility module is created at
the package root level. Decision deferred.

---

*This document is informational only. No architectural changes are authorized
without a corresponding ADR or specification update.*
