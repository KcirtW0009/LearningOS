"""test_state_models — UserState, NodeState, and HistoryEntry dataclasses."""
import sys
sys.path.insert(0, ".")

from dataclasses import FrozenInstanceError

from los.state.models import (
    UserState, NodeState, NodeStatus, HistoryEntry, CURRENT_SCHEMA_VERSION,
)


print("=== test_state_models ===")
print()

# ── 1. NodeState: default status = NOT_STARTED ──────────────────────
ns = NodeState(node_id="n1")
assert ns.status == NodeStatus.NOT_STARTED
assert ns.score == 0
assert ns.evidence == []
assert ns.is_completed is False
print("1. NodeState defaults OK")

# ── 2. NodeState: reject empty node_id ──────────────────────────────
try:
    NodeState(node_id="")
    assert False, "should have raised"
except ValueError as e:
    assert "node_id" in str(e)
print("2. Reject empty NodeState.node_id OK")

# ── 3. NodeState: reject whitespace-only node_id ────────────────────
try:
    NodeState(node_id="   ")
    assert False
except ValueError as e:
    assert "node_id" in str(e)
print("3. Reject whitespace NodeState.node_id OK")

# ── 4. NodeState: reject negative score ─────────────────────────────
try:
    NodeState(node_id="n", score=-1)
    assert False
except ValueError as e:
    assert "score" in str(e).lower()
print("4. Reject negative NodeState.score OK")

# ── 5. NodeState: is_completed for COMPLETED ────────────────────────
ns2 = NodeState(node_id="done", status=NodeStatus.COMPLETED)
assert ns2.is_completed is True
print("5. NodeState.is_completed COMPLETED OK")

# ── 6. NodeState: is_completed for MASTERED ─────────────────────────
ns3 = NodeState(node_id="master", status=NodeStatus.MASTERED)
assert ns3.is_completed is True
print("6. NodeState.is_completed MASTERED OK")

# ── 7. NodeState: is_completed for NOT_STARTED ──────────────────────
assert ns.is_completed is False
print("7. NodeState.is_completed NOT_STARTED OK")

# ── 8. NodeState: updated_at auto-populated ─────────────────────────
ns4 = NodeState(node_id="auto-time")
assert ns4.updated_at != ""
assert "T" in ns4.updated_at
print(f"8. NodeState updated_at auto-populated OK ({ns4.updated_at})")

# ── 9. UserState: defaults ──────────────────────────────────────────
us = UserState()
assert us.user_id == "default"
assert us.graph_id == ""
assert us.graph_version == ""
assert us.node_states == {}
assert us.history == []
assert us.schema_version == CURRENT_SCHEMA_VERSION
# graph_path removed in Phase 4 — now owned by RuntimeManifest
print("9. UserState defaults OK")

# ── 10. UserState: created_at auto-populated ────────────────────────
assert us.created_at != ""
assert "T" in us.created_at
print(f"10. UserState created_at auto-populated OK ({us.created_at})")

# ── 11. UserState: updated_at auto-populated ────────────────────────
assert us.updated_at != ""
assert "T" in us.updated_at
print(f"11. UserState updated_at auto-populated OK ({us.updated_at})")

# ── 12. UserState: ensure_node_state creates entry ──────────────────
ns_new = us.ensure_node_state("new-node")
assert ns_new.node_id == "new-node"
assert ns_new.status == NodeStatus.NOT_STARTED
assert "new-node" in us.node_states
print("12. UserState.ensure_node_state creates entry OK")

# ── 13. UserState: ensure_node_state idempotent ─────────────────────
ns_existing = us.ensure_node_state("new-node")
assert ns_existing is ns_new
print("13. UserState.ensure_node_state idempotent OK")

# ── 14. UserState: get_node_state ───────────────────────────────────
assert us.get_node_state("new-node") is ns_new
assert us.get_node_state("no-such") is None
print("14. UserState.get_node_state OK")

# ── 15. UserState: completed_count / total_count ────────────────────
us2 = UserState()
us2.ensure_node_state("a")
us2.ensure_node_state("b")
us2.ensure_node_state("c")
us2.node_states["a"].status = NodeStatus.COMPLETED
us2.node_states["b"].status = NodeStatus.MASTERED
assert us2.completed_count == 2
assert us2.total_count == 3
print("15. UserState completed_count=2 total_count=3 OK")

# ── 16. UserState: completed_count empty ────────────────────────────
us3 = UserState()
assert us3.completed_count == 0
assert us3.total_count == 0
print("16. UserState completed_count empty=0 OK")

# ── 17. HistoryEntry: valid construction ────────────────────────────
he = HistoryEntry(
    node_id="n1", field="status",
    old_value="NOT_STARTED", new_value="IN_PROGRESS",
    timestamp="2025-01-01T00:00:00",
)
assert he.node_id == "n1"
assert he.field == "status"
assert he.old_value == "NOT_STARTED"
assert he.new_value == "IN_PROGRESS"
print("17. HistoryEntry construction OK")

# ── 18. HistoryEntry: reject empty node_id ──────────────────────────
try:
    HistoryEntry(
        node_id="", field="status",
        old_value="x", new_value="y",
        timestamp="2025-01-01T00:00:00",
    )
    assert False
except ValueError as e:
    assert "node_id" in str(e)
print("18. Reject empty HistoryEntry.node_id OK")

# ── 19. HistoryEntry: reject empty field ────────────────────────────
try:
    HistoryEntry(
        node_id="n1", field="",
        old_value="x", new_value="y",
        timestamp="2025-01-01T00:00:00",
    )
    assert False
except ValueError as e:
    assert "field" in str(e)
print("19. Reject empty HistoryEntry.field OK")

# ── 20. HistoryEntry: reject empty timestamp ────────────────────────
try:
    HistoryEntry(
        node_id="n1", field="status",
        old_value="x", new_value="y",
        timestamp="",
    )
    assert False
except ValueError as e:
    assert "timestamp" in str(e)
print("20. Reject empty HistoryEntry.timestamp OK")

# ── 21. HistoryEntry: frozen (immutable) ────────────────────────────
try:
    he.node_id = "mutated"
    assert False
except FrozenInstanceError:
    pass
print("21. HistoryEntry frozen OK")

print()
print("All tests passed.")
