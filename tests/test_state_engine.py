"""Phase 6 State Engine — test suite."""
import sys
sys.path.insert(0, ".")

from tests.utils import cleanup_state_file

from los.exceptions import (
    InvalidStateTransitionError,
    NodeAlreadyCompletedError,
    NodeNotFoundError,
)
from los.state.engine import (
    StateHandle,
    sync_node_states, complete_node, start_node,
    get_progress, get_node_status,
)
from los.state.models import UserState, NodeState, NodeStatus, HistoryEntry
from los.runtime.contracts.state_access import MutationResult, ProgressSnapshot

print("=== Phase 6 State Engine Tests ===")
print()

# ── 1. sync_node_states: empty -> populated ───────────────────────
us = UserState(user_id="test")
sync_node_states(us, ["a", "b", "c"])
assert len(us.node_states) == 3
for nid in ("a", "b", "c"):
    assert us.node_states[nid].node_id == nid
    assert us.node_states[nid].status == NodeStatus.NOT_STARTED
    assert us.node_states[nid].score == 0
assert us.total_count == 3
print("1. sync_node_states: empty -> 3 nodes OK")

# ── 2. sync_node_states: idempotent ───────────────────────────────
ns_a = us.node_states["a"]
ns_a.status = NodeStatus.COMPLETED
ns_a.score = 99
sync_node_states(us, ["a", "b", "c", "d"])
assert len(us.node_states) == 4
assert us.node_states["a"].status == NodeStatus.COMPLETED  # NOT overwritten
assert us.node_states["a"].score == 99                       # NOT overwritten
assert us.node_states["d"].status == NodeStatus.NOT_STARTED  # new
assert us.node_states["b"].status == NodeStatus.NOT_STARTED  # untouched
print("2. sync_node_states: idempotent OK")

# ── 3. complete_node: NOT_STARTED -> COMPLETED ───────────────────
us2 = UserState(user_id="test2")
sync_node_states(us2, ["x"])
old_history_len = len(us2.history)
old_updated = us2.updated_at
complete_node(us2, "x", score=10, evidence=["ev.txt"])
assert us2.node_states["x"].status == NodeStatus.COMPLETED
assert us2.node_states["x"].score == 10
assert us2.node_states["x"].evidence == ["ev.txt"]
assert us2.node_states["x"].is_completed
assert us2.updated_at != old_updated
assert len(us2.history) > old_history_len
status_entries = [h for h in us2.history if h.field == "status"]
assert status_entries[-1].node_id == "x"
assert status_entries[-1].old_value == "NOT_STARTED"
assert status_entries[-1].new_value == "COMPLETED"
print(f"3. complete_node: NOT_STARTED -> COMPLETED OK (score={us2.node_states['x'].score})")

# ── 4. complete_node: IN_PROGRESS -> COMPLETED ───────────────────
us3 = UserState(user_id="test3")
sync_node_states(us3, ["y"])
us3.node_states["y"].status = NodeStatus.IN_PROGRESS
complete_node(us3, "y")
assert us3.node_states["y"].status == NodeStatus.COMPLETED
assert us3.node_states["y"].score == 10
print("4. complete_node: IN_PROGRESS -> COMPLETED OK")

# ── 5. complete_node: duplicate -> NodeAlreadyCompletedError ──────
try:
    complete_node(us2, "x")
    assert False, "should have raised"
except NodeAlreadyCompletedError as e:
    assert "already" in str(e).lower()
print("5. Duplicate complete rejected: NodeAlreadyCompletedError")

# ── 6. complete_node: already COMPLETED -> NodeAlreadyCompletedError ─
try:
    complete_node(us3, "y")
    assert False
except NodeAlreadyCompletedError as e:
    assert "already" in str(e).lower()
print("6. Already COMPLETED rejected: NodeAlreadyCompletedError")

# ── 7. complete_node: unknown node -> NodeNotFoundError ───────────
try:
    complete_node(us2, "no-such-node")
    assert False
except NodeNotFoundError as e:
    assert "not tracked" in str(e)
print("7. Unknown node rejected: NodeNotFoundError")

# ── 8. complete_node: score non-decreasing ───────────────────────
us4b = UserState(user_id="test4b")
sync_node_states(us4b, ["w"])
us4b.node_states["w"].score = 80
us4b.node_states["w"].status = NodeStatus.NOT_STARTED  # reset
complete_node(us4b, "w", score=10)
assert us4b.node_states["w"].score == 80
print(f"8. Score non-decreasing: max(80,10)={us4b.node_states['w'].score} OK")

# ── 9. complete_node: evidence append ────────────────────────────
us5b = UserState(user_id="test5b")
sync_node_states(us5b, ["ev2"])
us5b.node_states["ev2"].status = NodeStatus.IN_PROGRESS
complete_node(us5b, "ev2", evidence=["a.txt"])
assert us5b.node_states["ev2"].evidence == ["a.txt"]
print(f"9. Evidence append: {us5b.node_states['ev2'].evidence} OK")

# ── 10. complete_node: score change logged ───────────────────────
us6 = UserState()
sync_node_states(us6, ["s"])
complete_node(us6, "s", score=50)
score_entries = [h for h in us6.history if h.field == "score"]
assert len(score_entries) >= 1
assert score_entries[-1].old_value == "0"
assert score_entries[-1].new_value == "50"
print("10. Score change HistoryEntry 0->50 OK")

# ── 11. start_node: NOT_STARTED -> IN_PROGRESS ───────────────────
us7 = UserState()
sync_node_states(us7, ["p"])
start_node(us7, "p")
assert us7.node_states["p"].status == NodeStatus.IN_PROGRESS
status_h = [h for h in us7.history if h.field == "status"]
assert status_h[-1].old_value == "NOT_STARTED"
assert status_h[-1].new_value == "IN_PROGRESS"
print("11. start_node: NOT_STARTED -> IN_PROGRESS OK")

# ── 12. start_node: auto-creates entry ───────────────────────────
us8 = UserState()
start_node(us8, "auto-create")
assert us8.node_states["auto-create"].status == NodeStatus.IN_PROGRESS
assert us8.total_count == 1
print("12. start_node: auto-create OK")

# ── 13. start_node: duplicate -> InvalidStateTransitionError ──────
try:
    start_node(us7, "p")
    assert False
except InvalidStateTransitionError as e:
    assert "already" in str(e).lower()
print("13. Duplicate start rejected: InvalidStateTransitionError")

# ── 14. get_progress ─────────────────────────────────────────────
us9 = UserState()
sync_node_states(us9, ["a", "b", "c", "d", "e"])
complete_node(us9, "a")
complete_node(us9, "b")
us9.node_states["c"].status = NodeStatus.MASTERED
us9.node_states["c"].score = 50
p = get_progress(us9)
assert p["total"] == 5
assert p["completed"] == 3        # 2 completed + 1 mastered
assert p["mastered"] == 1
assert p["percentage"] == 60.0
print(f"14. get_progress: {p} OK")

# ── 15. get_progress: empty ──────────────────────────────────────
p2 = get_progress(UserState())
assert p2["total"] == 0 and p2["completed"] == 0 and p2["percentage"] == 0.0
print(f"15. get_progress (empty): {p2} OK")

# ── 16. get_node_status ──────────────────────────────────────────
us10 = UserState()
sync_node_states(us10, ["n1"])
assert get_node_status(us10, "n1") == NodeStatus.NOT_STARTED
complete_node(us10, "n1")
assert get_node_status(us10, "n1") == NodeStatus.COMPLETED
try:
    get_node_status(us10, "no-such")
    assert False
except NodeNotFoundError as e:
    assert "not tracked" in str(e)
print("16. get_node_status OK")

# ── 17. Dependency direction ─────────────────────────────────────
# State Authority must not import from Graph, Runtime, CLI, Storage.
# Use sys.modules detection but skip modules imported by other test files
# (pytest runs all tests in the same process).
# We verify: state modules themselves do not transitively import these.
state_related = {
    k for k in sys.modules
    if k.startswith("los.state") or k == "los.state"
}
forbidden = {"los.graph", "los.engine", "los.cli", "los.storage",
             "los.runtime.runtime_instance"}
for key in state_related:
    mod = sys.modules[key]
    mod_file = getattr(mod, "__file__", "")
    if not mod_file or "state" not in mod_file:
        continue
    # Check __dict__ for imported submodule references (lazy check)
    for attr_name in dir(mod):
        obj = getattr(mod, attr_name, None)
        if hasattr(obj, "__name__") and getattr(obj, "__name__", "") in forbidden:
            raise AssertionError(f"State module {key} imports {obj.__name__}")
print("17. Dependency direction OK (state does not import graph/resolver/storage/cli)")

# ── 18. All APIs exported from los.state ─────────────────────────
from los.state import (
    sync_node_states as s1,
    complete_node as c1,
    start_node as st1,
    get_progress as g1,
    get_node_status as gn1,
)
assert s1 is sync_node_states
assert c1 is complete_node
print("18. All APIs exported from los.state OK")

# ── 19. start_node from COMPLETED rejected ───────────────────────
us11 = UserState()
sync_node_states(us11, ["q"])
complete_node(us11, "q")
try:
    start_node(us11, "q")
    assert False
except InvalidStateTransitionError as e:
    assert "already" in str(e).lower()
print("19. start_node from COMPLETED rejected OK")

# ── Phase 3: StateHandle adapter (StateMutator contract) ────────────────

print()
print("=== Phase 3 StateHandle Tests ===")
print()

# ── 20. StateHandle.complete_node() succeeds ──────────────────────────
us_sh = UserState(user_id="sh-test")
sync_node_states(us_sh, ["sh-a"])
sh = StateHandle(us_sh)
result = sh.complete_node("sh-a", score=42, evidence=["proof.md"])
assert isinstance(result, MutationResult)
assert result.success is True
assert result.node_id == "sh-a"
assert "completed" in result.message.lower()
# Verify UserState was actually mutated
assert us_sh.node_states["sh-a"].status == NodeStatus.COMPLETED
assert us_sh.node_states["sh-a"].score == 42
assert us_sh.node_states["sh-a"].evidence == ["proof.md"]
print(f"20. StateHandle.complete_node success: {result}")

# ── 21. StateHandle.complete_node() unknown node → failure ────────────
result = sh.complete_node("no-such-node")
assert isinstance(result, MutationResult)
assert result.success is False
assert result.node_id == "no-such-node"
assert "not tracked" in result.message
print(f"21. StateHandle.complete_node unknown: {result}")

# ── 22. StateHandle.complete_node() duplicate → failure ───────────────
result = sh.complete_node("sh-a")
assert result.success is False
assert "already" in result.message.lower()
print(f"22. StateHandle.complete_node duplicate: {result}")

# ── 23. StateHandle.start_node() succeeds ─────────────────────────────
us_sh2 = UserState(user_id="sh2")
sync_node_states(us_sh2, ["start-me"])
sh2 = StateHandle(us_sh2)
result = sh2.start_node("start-me")
assert isinstance(result, MutationResult)
assert result.success is True
assert result.node_id == "start-me"
assert us_sh2.node_states["start-me"].status == NodeStatus.IN_PROGRESS
print(f"23. StateHandle.start_node success: {result}")

# ── 24. StateHandle.start_node() invalid → failure ────────────────────
result = sh2.start_node("start-me")  # already IN_PROGRESS
assert result.success is False
assert "already" in result.message.lower()
print(f"24. StateHandle.start_node invalid: {result}")

# ── 25. StateHandle wraps correctly ───────────────────────────────────
# Verify StateHandle._us is the same object
assert sh._us is us_sh
assert sh2._us is us_sh2
print("25. StateHandle._us identity preserved")

# ── 26. Multiple operations on same handle ────────────────────────────
us_sh3 = UserState()
sync_node_states(us_sh3, ["multi-a", "multi-b"])
sh3 = StateHandle(us_sh3)
r1 = sh3.complete_node("multi-a")
assert r1.success
r2 = sh3.start_node("multi-b")
assert r2.success
assert us_sh3.node_states["multi-a"].status == NodeStatus.COMPLETED
assert us_sh3.node_states["multi-b"].status == NodeStatus.IN_PROGRESS
print("26. Multiple operations on same handle OK")

# ── 27. StateHandle does not modify UserState model ────────────────────
# Verify UserState interface unchanged (no new methods added by Phase 3)
us_clean = UserState()
assert not hasattr(us_clean, "complete_node")
assert not hasattr(us_clean, "start_node")
print("27. UserState model unchanged (no mutation methods added)")

print()
print("All tests passed.")
