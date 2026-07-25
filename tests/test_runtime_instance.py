"""Phase 2 RuntimeInstance — test suite.

Minimum gate (Constraint 6):
  1. RuntimeInstance import succeeds
  2. RuntimeStatus exists
  3. RuntimeInstance.load() works
  4. RuntimeInstance.get_available_nodes() works
  5. RuntimeInstance.complete_node() works
"""
import os
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "runtime")

from tests.utils import (
    cleanup_state_file,
    fresh_state,
    load_example_graph,
    make_temp_graph,
)
from los.runtime.runtime_instance import RuntimeInstance, RuntimeStatus
from los.graph.loader import load_graph_package, LoadedGraph
from los.state.models import UserState
from los.state.engine import sync_node_states

print("=== Phase 2 RuntimeInstance Tests ===")
print()

# Clean state from previous runs
cleanup_state_file()

# ── 1. RuntimeInstance import succeeds ────────────────────────────
assert RuntimeInstance is not None
print("1. RuntimeInstance import OK")

# ── 2. RuntimeStatus exists ──────────────────────────────────────
assert RuntimeStatus.CREATED.value == "CREATED"
assert RuntimeStatus.ACTIVE.value == "ACTIVE"
assert len(list(RuntimeStatus)) == 5  # all 5 RS-002 states
print(f"2. RuntimeStatus OK ({len(list(RuntimeStatus))} states)")

# ── 3. RuntimeInstance.load() works ──────────────────────────────
ri = RuntimeInstance.load("graphs/example-basics")
assert ri.status == RuntimeStatus.ACTIVE
assert ri.runtime_id is not None
assert len(ri.runtime_id) == 12
assert isinstance(ri._graph, LoadedGraph)
assert ri._graph.package_id == "example-basics"
print(f"3. RuntimeInstance.load() OK (status={ri.status.value}, id={ri.runtime_id})")

# ── 4. RuntimeInstance.get_available_nodes() works ───────────────
avail = ri.get_available_nodes()
assert "node-a" in avail  # root, no blockers
assert "node-c" in avail  # association from A, non-blocking
assert "node-b" not in avail  # prerequisite from A, locked
print(f"4. get_available_nodes() OK: {avail}")

# ── 5. RuntimeInstance.complete_node() works ─────────────────────
result = ri.complete_node("node-a")
assert "Completed:" in result
assert "Node A" in result
assert "score: 10" in result
print(f"5. complete_node() OK: {result}")

# ── 6. After completing root, dependent becomes available ─────────
avail2 = ri.get_available_nodes()
assert "node-b" in avail2  # unlocked by completing node-a
print(f"6. Dependent unlocks OK: {avail2}")

# ── 7. get_node_detail returns expected structure ────────────────
detail = ri.get_node_detail("node-a")
assert detail is not None
assert detail["id"] == "node-a"
assert detail["title"] == "Node A"
assert detail["status"] == "COMPLETED"
assert detail["score"] == 10
assert detail["type"] == "concept"
assert detail["difficulty"] == "beginner"
print(f"7. get_node_detail() OK")

# ── 8. get_node_detail returns None for unknown node ─────────────
assert ri.get_node_detail("no-such-node") is None
print("8. get_node_detail() unknown → None OK")

# ── 9. get_progress returns expected keys ────────────────────────
progress = ri.get_progress()
assert "total" in progress
assert "completed" in progress
assert "mastered" in progress
assert "percentage" in progress
assert "available" in progress
assert "locked" in progress
assert progress["total"] == 3
assert progress["completed"] == 1
print(f"9. get_progress() OK: {progress}")

# ── 10. get_graph_info returns expected keys ─────────────────────
info = ri.get_graph_info()
assert info["package_id"] == "example-basics"
assert info["package_name"] == "Example Basics"
assert info["node_count"] == 3
assert info["edge_count"] == 2
print(f"10. get_graph_info() OK: {info['package_name']} v{info['package_version']}")

# ── 11. complete_node: locked node → ValueError ──────────────────
try:
    # Reload fresh — node-b depends on node-a
    cleanup_state_file()
    ri_fresh = RuntimeInstance.load("graphs/example-basics")
    ri_fresh.complete_node("node-b")
    assert False, "Should have raised ValueError"
except ValueError as e:
    assert "Cannot complete 'node-b'" in str(e)
    assert "Prerequisite not met" in str(e)
    print(f"11. complete_node locked → ValueError OK: {e}")

# ── 12. complete_node: already completed → ValueError ────────────
try:
    ri_fresh.complete_node("node-a")  # first time OK
    ri_fresh.complete_node("node-a")  # second time → error
    assert False, "Should have raised ValueError"
except ValueError as e:
    assert "Cannot complete 'node-a'" in str(e)
    assert "already" in str(e).lower()
    print(f"12. complete_node already → ValueError OK: {e}")

# ── 13. complete_node: unknown node → ValueError ─────────────────
try:
    ri_fresh.complete_node("no-such-node")
    assert False, "Should have raised ValueError"
except ValueError as e:
    assert "Cannot complete 'no-such-node'" in str(e)
    assert "Unknown node" in str(e)
    print(f"13. complete_node unknown → ValueError OK: {e}")

# ── 14. _transition gate: invalid transition → error ─────────────
from los.exceptions import InvalidStateTransitionError

try:
    ri._transition(RuntimeStatus.CREATED)  # ACTIVE → CREATED not allowed
    assert False, "Should have raised InvalidStateTransitionError"
except InvalidStateTransitionError as e:
    assert "Cannot transition" in str(e)
print(f"14. _transition invalid → InvalidStateTransitionError OK")

# ── 15. _transition gate: direct _status bypass is blocked ───────
# Verify that status is a property (read-only)
assert isinstance(type(ri).status, property)
print("15. status is read-only property OK")

# ── 16. RuntimeInstance satisfies ResolutionInput (structural) ───
from los.engine.resolver import compute_availability, can_complete_node, get_available_nodes

# compute_availability expects ResolutionInput Protocol
statuses = compute_availability(ri)
assert "node-a" in statuses
assert "node-b" in statuses
assert "node-c" in statuses
print(f"16. compute_availability(RuntimeInstance) OK: {statuses}")

# ── 17. can_complete_node(RuntimeInstance) works ─────────────────
cleanup_state_file()
ri2 = RuntimeInstance.load("graphs/example-basics")
ok, _ = can_complete_node(ri2, "node-a")
assert ok
ok2, reason = can_complete_node(ri2, "node-b")
assert not ok2
print(f"17. can_complete_node(RuntimeInstance) OK (node-b: {reason})")

# ── 18. get_available_nodes(RuntimeInstance) works ───────────────
avail3 = get_available_nodes(ri2)
assert "node-a" in avail3
print(f"18. get_available_nodes(RuntimeInstance) OK: {avail3}")

# ── 19. runtime_id is unique per instance ────────────────────────
cleanup_state_file()
ri_a = RuntimeInstance.load("graphs/example-basics")
cleanup_state_file()
ri_b = RuntimeInstance.load("graphs/example-basics")
assert ri_a.runtime_id != ri_b.runtime_id
print(f"19. Unique runtime_id OK: {ri_a.runtime_id} != {ri_b.runtime_id}")

# ── 20. Constructor creates CREATED status ───────────────────────
g, us = load_example_graph()
ri_created = RuntimeInstance(g, us)
assert ri_created.status == RuntimeStatus.CREATED
print(f"20. Constructor → CREATED status OK")

# ── Phase 3: State Authority Completion ─────────────────────────────────

print()
print("=== Phase 3 RuntimeInstance Tests ===")
print()

# ── 21. get_progress_snapshot() returns ProgressSnapshot ───────────────
from los.runtime.contracts.state_access import ProgressSnapshot
cleanup_state_file()
ri_p3 = RuntimeInstance.load("graphs/example-basics")
ri_p3.complete_node("node-a")
snap = ri_p3.get_progress_snapshot()
assert isinstance(snap, ProgressSnapshot)
assert snap.total == 3
assert snap.completed == 1
assert snap.mastered == 0
assert snap.percentage == 33.3
print(f"21. get_progress_snapshot: {snap}")

# ── 22. snapshot values match get_progress() ───────────────────────────
progress = ri_p3.get_progress()
assert snap.total == progress["total"]
assert snap.completed == progress["completed"]
assert snap.mastered == progress["mastered"]
assert snap.percentage == progress["percentage"]
print("22. snapshot values match get_progress()")

# ── 23. get_progress_snapshot() on empty state ─────────────────────────
cleanup_state_file()
ri_empty = RuntimeInstance.load("graphs/example-basics")
snap_empty = ri_empty.get_progress_snapshot()
assert snap_empty.total == 3
assert snap_empty.completed == 0
assert snap_empty.percentage == 0.0
print(f"23. empty snapshot: {snap_empty}")

# ── 24. complete_node mutation uses StateMutator boundary ──────────────
# RuntimeInstance._mutator must exist (set in __init__)
assert hasattr(ri_p3, "_mutator")
from los.state.engine import StateHandle
assert isinstance(ri_p3._mutator, StateHandle)
print("24. _mutator is StateHandle instance")

# ── 25. AST audit: RuntimeInstance does NOT import state mutation fns ──
import ast, os
ri_path = os.path.join("runtime", "los", "runtime", "runtime_instance.py")
with open(ri_path, encoding="utf-8") as f:
    ri_tree = ast.parse(f.read())
ri_imports = set()
for node in ast.walk(ri_tree):
    if isinstance(node, ast.ImportFrom) and node.module:
        for alias in node.names:
            ri_imports.add(f"{node.module}.{alias.name}")
# Allowed: StateHandle, sync_node_states, get_progress
# Forbidden: complete_node, start_node as direct imports from state.engine
assert "los.state.engine.StateHandle" in ri_imports, "StateHandle must be imported"
assert "los.state.engine.complete_node" not in ri_imports, "MUST NOT import complete_node"
assert "los.state.engine.start_node" not in ri_imports, "MUST NOT import start_node"
print("25. AST audit: StateHandle OK, complete_node ABSENT, start_node ABSENT")

# ── 26. MutationResult failure → ValueError with correct format ────────
cleanup_state_file()
ri_val = RuntimeInstance.load("graphs/example-basics")
ri_val.complete_node("node-a")  # first time OK
try:
    ri_val.complete_node("node-a")  # should fail through StateHandle
    assert False, "Should have raised ValueError"
except ValueError as e:
    assert "Cannot complete 'node-a'" in str(e)
    assert "already" in str(e).lower()
    print(f"26. MutationResult failure → ValueError: {e}")

# ── 27. CLI output format unchanged after refactor ─────────────────────
cleanup_state_file()
ri_fmt = RuntimeInstance.load("graphs/example-basics")
msg = ri_fmt.complete_node("node-a")
assert "Completed:" in msg
assert "Node A" in msg
assert "score:" in msg
print(f"27. CLI format unchanged: {msg}")

# ── 28. Complete all nodes → full progress ────────────────────────────
cleanup_state_file()
ri_fmt2 = RuntimeInstance.load("graphs/example-basics")
ri_fmt2.complete_node("node-a")
ri_fmt2.complete_node("node-b")
ri_fmt2.complete_node("node-c")
snap_full = ri_fmt2.get_progress_snapshot()
assert snap_full.completed == 3
assert snap_full.percentage == 100.0
print("28. Full completion: 3/3 → 100%")

# ══════════════════════════════════════════════════════════════════════
# Phase 4 — Persistence & Recovery
# ══════════════════════════════════════════════════════════════════════

from los.runtime.runtime_manifest import DEFAULT_MANIFEST_PATH, RuntimeManifest

# ── 29. load() creates and persists RuntimeManifest ────────────────────
cleanup_state_file()
import os as _os
_manifest_path_file = _os.path.join("data", "runtime-manifest.json")
if _os.path.isfile(_manifest_path_file):
    _os.remove(_manifest_path_file)

ri_p4a = RuntimeInstance.load("graphs/example-basics")
assert _os.path.isfile(_manifest_path_file), "Manifest file not created"
raw = __import__("json").load(open(_manifest_path_file))
assert raw["graph_path"] == "graphs/example-basics"
assert raw["graph_id"] == "example-basics"
assert raw["runtime_id"] != ""
print(f"29. Manifest created on load: {raw['runtime_id']}")

# ── 30. resume() restores from persisted manifest ──────────────────────
ri_p4a.complete_node("node-a")
ri_p4a.save()
ri_p4b = RuntimeInstance.resume()
assert ri_p4b is not None
assert ri_p4b.get_progress()["completed"] == 1
info = ri_p4b.get_graph_info()
assert info["package_id"] == "example-basics"
assert ri_p4b.status == RuntimeStatus.ACTIVE
print("30. Resume restores state: 1/3 completed")

# ── 31. resume() preserves runtime_id ──────────────────────────────────
ri_p4c = RuntimeInstance.load("graphs/example-basics")
original_id = ri_p4c._runtime_id
ri_p4c.save()
ri_p4d = RuntimeInstance.resume()
assert ri_p4d is not None
assert ri_p4d._runtime_id == original_id
print(f"31. Runtime ID preserved: {original_id}")

# ── 32. resume() without manifest returns None ─────────────────────────
if _os.path.isfile(_manifest_path_file):
    _os.remove(_manifest_path_file)
ri_p4e = RuntimeInstance.resume()
assert ri_p4e is None
print("32. No manifest → None")

# ── 33. resume() with moved graph → RecoveryError ──────────────────────
from los.exceptions import RecoveryError

ri_p4f = RuntimeInstance.load("graphs/example-basics")
ri_p4f.save()
raw2 = __import__("json").load(open(_manifest_path_file))
raw2["graph_path"] = "graphs/does-not-exist"
__import__("json").dump(raw2, open(_manifest_path_file, "w"))

try:
    RuntimeInstance.resume()
    assert False, "Expected RecoveryError"
except RecoveryError as e:
    assert "not found" in str(e).lower()
    print(f"33. Moved graph → RecoveryError: {e}")

# Restore correct manifest
_os.remove(_manifest_path_file)

# ── 34. manifest last_active updated on save ───────────────────────────
ri_p4g = RuntimeInstance.load("graphs/example-basics")
ri_p4g.save()
raw3 = __import__("json").load(open(_manifest_path_file))
assert raw3["last_active"] != ""
print(f"34. last_active updated: {raw3['last_active'][:19]}")

# ── 35. UserState no longer has graph_path ─────────────────────────────
from los.state.models import UserState
us_check = UserState()
assert not hasattr(us_check, "graph_path"), "graph_path should be removed from UserState"
print("35. UserState has no graph_path OK")

print()
print("All tests passed.")
