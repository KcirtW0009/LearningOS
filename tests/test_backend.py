"""Comprehensive backend diagnostic test."""
import sys, os, traceback, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "runtime"))
os.environ["LEARNINGOS_PROJECT_ROOT"] = os.path.dirname(__file__)

from los.runtime.runtime_instance import RuntimeInstance
from los.engine.xp import BASE_XP, get_level, xp_to_next_level, calculate_xp
from los.engine.achievements import check_achievements

graphs_dir = os.path.join(os.path.dirname(__file__), "graphs")

print("=" * 60)
print("TEST 1: XP Formula")
print("=" * 60)
print(f"BASE_XP: {BASE_XP}")
xp_one_node = calculate_xp("beginner", 10, 0)
print(f"1 node (score=10, beginner): {xp_one_node} XP")
print(f"  Level at {xp_one_node} XP: Lv.{get_level(xp_one_node)}")
print(f"  XP to next: {xp_to_next_level(xp_one_node)}")
print(f"  Expecting: Lv.2, XP to next >= 0")
assert get_level(xp_one_node) == 2, f"Expected Lv.2, got Lv.{get_level(xp_one_node)}"
print("  PASSED")

xp_three = calculate_xp("beginner", 10, 0) * 4
print(f"\n4 nodes (score=10 each, beginner): {xp_three} XP")
print(f"  Level: Lv.{get_level(xp_three)}")
assert get_level(xp_three) == 3, f"Expected Lv.3, got Lv.{get_level(xp_three)}"
print("  PASSED")

print(f"\nLevel progression check:")
for xp_val in [0, 50, 200, 450, 800, 1250, 5000, 20000, 125000]:
    lv = get_level(xp_val)
    print(f"  {xp_val:>6} XP → Lv.{lv}")

# Verify: Lv.1→Lv.2 needs 50 XP (1 node)
assert get_level(0) == 1
assert get_level(49) == 1
assert get_level(50) == 2
# Verify: Lv.2→Lv.3 needs 200 XP (4 beginner nodes)
assert get_level(199) == 2
assert get_level(200) == 3
print("  All level progression assertions passed")

print()
print("=" * 60)
print("TEST 2: add_score_event + COMPLETED auto-promotion")
print("=" * 60)
for gname in sorted(os.listdir(graphs_dir)):
    gpath = os.path.join(graphs_dir, gname)
    if not os.path.isdir(gpath):
        continue
    print(f"\nGraph: {gname}")
    runtime = RuntimeInstance.load(gpath)
    nodes = runtime.get_node_ids()
    target = nodes[0]
    
    # Test score event
    msg = runtime.add_score_event(target, 5, "test")
    ns = runtime._state.get_node_state(target)
    print(f"  Node {target}: status={ns.status.value}, score={ns.score}")
    assert ns.status.value == "COMPLETED", f"Expected COMPLETED, got {ns.status.value}"
    print(f"  PASSED: Score {ns.score} → {ns.status.value}")
    
    # Test undo
    msg = runtime.undo_last_action()
    ns2 = runtime._state.get_node_state(target)
    print(f"  After undo: status={ns2.status.value}, score={ns2.score}")
    print(f"  Undo result: {msg}")
    assert ns2.score == 5, f"Expected score 5, got {ns2.score}"
    break

print()
print("=" * 60)
print("TEST 3: Cross-graph achievements & global state")
print("=" * 60)
from los.api.server import _compute_global_state
gs = _compute_global_state()
print(json.dumps({k: v for k, v in gs.items() if k != "all_node_scores"}, indent=2))
print()

# Test with achievements
from los.state.models import UserState
us = UserState(user_id="default", graph_id="test")
results = check_achievements(us, global_state=gs)
earned = [a.name for a, ok in results if ok]
locked = [a.name for a, ok in results if not ok]
print(f"Earned ({len(earned)}):", earned)
print(f"Locked ({len(locked)}):", locked)

print()
print("ALL TESTS PASSED")
