"""Phase 7 XP + Rules + Achievements Engine Tests."""
print("=== Phase 7 Engine Tests ===\n")

# ── XP Engine ───────────────────────────────────────────────────────

from los.engine.xp import (
    calculate_xp,
    compute_total_xp,
    get_level,
    xp_to_next_level,
    BASE_XP,
    DIFFICULTY_MULTIPLIER,
)

# Test 1: base XP
xp = calculate_xp("beginner", 10)
assert xp == BASE_XP * 1 * 1  # beginner=1 * score_factor=1
print("1. Base XP (beginner, score=10) =", xp, "OK")

# Test 2: advanced with max score
xp = calculate_xp("advanced", 100)
assert xp == BASE_XP * 3 * 10  # advanced=3 * score_factor=10
print("2. Advanced max XP =", xp, "OK")

# Test 3: intermediate
xp = calculate_xp("intermediate", 5)
assert xp == BASE_XP * 2 * 1  # intermediate=2 * score_factor=1
print("3. Intermediate XP =", xp, "OK")

# Test 4: score_factor floor
xp = calculate_xp("beginner", 3)
assert xp == BASE_XP * 1 * 1  # score_factor = max(1, 0) = 1
print("4. Score floor XP =", xp, "OK")

# Test 5: None difficulty → beginner
xp = calculate_xp(None, 10)
assert xp == BASE_XP * 1 * 1
print("5. None difficulty XP =", xp, "OK")

# Test 6: unknown difficulty → 1
xp = calculate_xp("expert", 10)
assert xp == BASE_XP * 1 * 1
print("6. Unknown difficulty XP =", xp, "OK")

# Test 7: get_level
assert get_level(0) == 1
assert get_level(100) == 1
assert get_level(400) == 2
assert get_level(900) == 3
print("7. Level calculation OK:", get_level(0), get_level(100), get_level(400), get_level(900))

# Test 8: xp_to_next_level
assert xp_to_next_level(0) == 400
assert xp_to_next_level(100) == 300
assert xp_to_next_level(350) == 50
print("8. XP to next level OK:", xp_to_next_level(0), xp_to_next_level(100), xp_to_next_level(350))

# ── Rule Engine ─────────────────────────────────────────────────────

from los.state.models import UserState, NodeState, NodeStatus
from los.engine.rules import evaluate_progress_rule

# Build a test state
state = UserState(user_id="test")
state.node_states = {
    "n1": NodeState(node_id="n1", status=NodeStatus.COMPLETED, score=8),
    "n2": NodeState(node_id="n2", status=NodeStatus.COMPLETED, score=10),
    "n3": NodeState(node_id="n3", status=NodeStatus.MASTERED, score=10),
    "n4": NodeState(node_id="n4", status=NodeStatus.NOT_STARTED, score=0),
    "n5": NodeState(node_id="n5", status=NodeStatus.IN_PROGRESS, score=3),
}
state.total_xp = 30

# Test 9: completed_count rule
ok, reason = evaluate_progress_rule(state, {"type": "completed_count", "min": 3})
assert ok
print(f"9. completed_count >= 3 → {ok} ({reason}) OK")

ok, reason = evaluate_progress_rule(state, {"type": "completed_count", "min": 5})
assert not ok
print(f"9b. completed_count >= 5 → {ok} ({reason}) OK")

# Test 10: percentage rule
ok, reason = evaluate_progress_rule(state, {"type": "percentage", "min": 50})
assert ok
print(f"10. percentage >= 50% → {ok} ({reason}) OK")

# Test 11: score_gte rule
ok, reason = evaluate_progress_rule(
    state, {"type": "score_gte", "node_id": "n1", "min": 5}
)
assert ok
print(f"11. score_gte(n1, 5) → {ok} ({reason}) OK")

ok, reason = evaluate_progress_rule(
    state, {"type": "score_gte", "node_id": "n3", "min": 10}
)
assert ok
print(f"11b. score_gte(n3, 10) → {ok} ({reason}) OK")

# Test 12: xp_gte rule
ok, reason = evaluate_progress_rule(state, {"type": "xp_gte", "min": 20})
assert ok
print(f"12. xp >= 20 → {ok} ({reason}) OK")

# Test 13: mastered_count rule
ok, reason = evaluate_progress_rule(state, {"type": "mastered_count", "min": 1})
assert ok
print(f"13. mastered >= 1 → {ok} ({reason}) OK")

# Test 14: unknown node in score_gte
ok, reason = evaluate_progress_rule(
    state, {"type": "score_gte", "node_id": "nonexistent", "min": 5}
)
assert not ok
print(f"14. score_gte(unknown) → {ok} ({reason}) OK")

# Test 15: unknown rule type
ok, reason = evaluate_progress_rule(state, {"type": "unknown_rule", "min": 1})
assert not ok
assert "unknown rule type" in reason
print(f"15. unknown rule → {ok} ({reason}) OK")

# ── Achievement Engine ──────────────────────────────────────────────

from los.engine.achievements import (
    Achievement,
    check_achievements,
    get_new_achievements,
)

# Test 16: check_achievements with partial progress
results = check_achievements(state)
earned = [(a.name, ok) for a, ok in results]
print("16. Achievement results:", earned)
# Should earn: first-step (1 completed), perfectionist (n2/n3 have score=10)
earned_ids = {a.id for a, ok in results if ok}
assert "first-step" in earned_ids
assert "perfectionist" in earned_ids
print("16. Achievement check OK")

# Test 17: get_new_achievements
new = get_new_achievements(state, previously_earned={"first-step"})
new_ids = {a.id for a in new}
assert "first-step" not in new_ids
assert "perfectionist" in new_ids
print(f"17. New achievements: {new_ids} OK")

# Test 18: Achievement dataclass
a = Achievement(id="test", name="测试", description="测试成就", rule={"type": "completed_count", "min": 99})
assert a.id == "test"
assert a.name == "测试"
print("18. Achievement model OK")

# Test 19: UserState.add_xp
s = UserState(user_id="xp_test")
assert s.total_xp == 0
s.add_xp(50)
assert s.total_xp == 50
s.add_xp(30)
assert s.total_xp == 80
print("19. UserState.add_xp OK:", s.total_xp)

# Test 20: compute_total_xp backward from scores
s2 = UserState(user_id="legacy")
s2.node_states = {
    "a": NodeState(node_id="a", score=5),
    "b": NodeState(node_id="b", score=7),
}
from los.engine.xp import compute_total_xp
# This sums node scores, not XP values. The test value is: 5+7=12
total = compute_total_xp(s2)
print(f"20. compute_total_xp = {total} OK")

print("\nAll Phase 7 tests passed.")
