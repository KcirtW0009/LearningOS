"""Phase 7 Runtime Engine Resolver — test suite."""
import ast
import os
import sys

import yaml

sys.path.insert(0, ".")

from tests.utils import (
    cleanup_state_file,
    fresh_state,
    load_example_graph,
    make_temp_graph,
)
from los.engine.resolver import (
    compute_availability,
    get_available_nodes,
    can_complete_node,
)
from los.runtime.runtime_instance import RuntimeInstance
from los.graph.loader import load_graph_package
from los.state.engine import sync_node_states, complete_node
from los.state.models import UserState, NodeStatus

print("=== Phase 7 Resolver Tests ===")
print()

# ── helpers ────────────────────────────────────────────────────────────

graph, us = load_example_graph()
# graph has: node-a (root), node-b (prerequisite from a), node-c (association from a)


def make_ri(g, s):
    """Create a RuntimeInstance wrapping (graph, state) for resolver tests."""
    return RuntimeInstance(g, s)


# ── 1. Root node is AVAILABLE ──────────────────────────────────────────
statuses = compute_availability(make_ri(graph, us))
assert statuses["node-a"] == "AVAILABLE", f"got {statuses['node-a']}"
print("1. Root node → AVAILABLE")

# ── 2. Single prerequisite: source not completed → LOCKED ──────────────
# node-b has prerequisite: node-a (NOT_STARTED)
assert statuses["node-b"] == "LOCKED", f"got {statuses['node-b']}"
print("2. A→B with A NOT_STARTED → B LOCKED")

# ── 3. Single prerequisite: source completed → AVAILABLE ───────────────
complete_node(us, "node-a")
statuses2 = compute_availability(make_ri(graph, us))
assert statuses2["node-b"] == "AVAILABLE", f"got {statuses2['node-b']}"
print("3. A→B with A COMPLETED → B AVAILABLE")

# ── 4. Multiple prerequisites (AND): partial → LOCKED ──────────────────
# Build a graph with C depending on both A and B
td = make_temp_graph(
    nodes=[
        {"id": "a", "title": "A", "description": "A"},
        {"id": "b", "title": "B", "description": "B"},
        {"id": "c", "title": "C", "description": "C"},
    ],
    edges=[
        {"from": "a", "to": "c", "relation": "prerequisite"},
        {"from": "b", "to": "c", "relation": "prerequisite"},
    ],
    package_id="multi",
    name="Multi",
)
g_multi = load_graph_package(td)
us_multi = UserState()
sync_node_states(us_multi, [n.id for n in g_multi.get_all_nodes()])
# Complete only A
complete_node(us_multi, "a")
s_partial = compute_availability(make_ri(g_multi, us_multi))
assert s_partial["c"] == "LOCKED", f"Partial prerequisites: got {s_partial['c']}"
assert s_partial["a"] == "COMPLETED"
assert s_partial["b"] == "AVAILABLE"  # root, no prereqs
print("4. A&B→C with only A done → C LOCKED (AND semantics)")

# ── 5. Multiple prerequisites (AND): all satisfied → AVAILABLE ─────────
complete_node(us_multi, "b")
s_all = compute_availability(make_ri(g_multi, us_multi))
assert s_all["c"] == "AVAILABLE", f"All prerequisites: got {s_all['c']}"
print("5. A&B→C with both done → C AVAILABLE")

# ── 6. dependency relation blocks ──────────────────────────────────────
td2 = make_temp_graph(
    nodes=[
        {"id": "x", "title": "X", "description": "X"},
        {"id": "y", "title": "Y", "description": "Y"},
    ],
    edges=[{"from": "x", "to": "y", "relation": "dependency"}],
    package_id="dep",
    name="D",
)
g_dep = load_graph_package(td2)
us_dep = UserState()
sync_node_states(us_dep, [n.id for n in g_dep.get_all_nodes()])
s_dep = compute_availability(make_ri(g_dep, us_dep))
assert s_dep["y"] == "LOCKED"
complete_node(us_dep, "x")
s_dep2 = compute_availability(make_ri(g_dep, us_dep))
assert s_dep2["y"] == "AVAILABLE"
print("6. dependency relation → blocking (same as prerequisite)")

# ── 7. progression relation blocks ─────────────────────────────────────
td3 = make_temp_graph(
    nodes=[
        {"id": "p1", "title": "P1", "description": "P1"},
        {"id": "p2", "title": "P2", "description": "P2"},
    ],
    edges=[{"from": "p1", "to": "p2", "relation": "progression"}],
    package_id="prog",
    name="P",
)
g_prog = load_graph_package(td3)
us_prog = UserState()
sync_node_states(us_prog, [n.id for n in g_prog.get_all_nodes()])
s_prog = compute_availability(make_ri(g_prog, us_prog))
assert s_prog["p2"] == "LOCKED"
complete_node(us_prog, "p1")
s_prog2 = compute_availability(make_ri(g_prog, us_prog))
assert s_prog2["p2"] == "AVAILABLE"
print("7. progression relation → blocking")

# ── 8. association does NOT block ──────────────────────────────────────
# node-c in example-basics has association from node-a
# node-a is COMPLETED, but association is non-blocking
assert statuses2["node-c"] == "AVAILABLE", f"association: got {statuses2['node-c']}"
print("8. association → non-blocking (C AVAILABLE regardless of A)")

# ── 9. alternative does NOT block ──────────────────────────────────────
td4 = make_temp_graph(
    nodes=[
        {"id": "m", "title": "M", "description": "M"},
        {"id": "n", "title": "N", "description": "N"},
    ],
    edges=[{"from": "m", "to": "n", "relation": "alternative"}],
    package_id="alt",
    name="Alt",
)
g_alt = load_graph_package(td4)
us_alt = UserState()
sync_node_states(us_alt, [n.id for n in g_alt.get_all_nodes()])
s_alt = compute_availability(make_ri(g_alt, us_alt))
assert s_alt["n"] == "AVAILABLE"  # alternative doesn't block
print("9. alternative → non-blocking")

# ── 10. IN_PROGRESS passes through ─────────────────────────────────────
# Use a fresh state on example-basics
graph2, us10 = load_example_graph()
sync_node_states(us10, [n.id for n in graph2.get_all_nodes()])
us10.node_states["node-a"].status = NodeStatus.IN_PROGRESS
s = compute_availability(make_ri(graph2, us10))
assert s["node-a"] == "IN_PROGRESS"
print("10. IN_PROGRESS → passed through")

# ── 11. COMPLETED passes through ───────────────────────────────────────
# node-a is already COMPLETED in 'us'
assert statuses2["node-a"] == "COMPLETED"
print("11. COMPLETED → passed through")

# ── 12. MASTERED unlocks same as COMPLETED ─────────────────────────────
graph_m, us_m = load_example_graph()
sync_node_states(us_m, [n.id for n in graph_m.get_all_nodes()])
us_m.node_states["node-a"].status = NodeStatus.MASTERED
us_m.node_states["node-a"].score = 50
s_m = compute_availability(make_ri(graph_m, us_m))
assert s_m["node-a"] == "MASTERED"
assert s_m["node-b"] == "AVAILABLE"  # unlocked by MASTERED
print("12. MASTERED prerequisite → unlocks dependent")

# ── 13. get_available_nodes excludes non-available ─────────────────────
avail = get_available_nodes(make_ri(graph2, us10))
assert "node-a" not in avail  # IN_PROGRESS
assert "node-b" not in avail
assert "node-c" in avail      # no incoming blockers
print(f"13. get_available_nodes: {avail}")

# ── 14. can_complete_node: success ─────────────────────────────────────
graph_c, us_c = load_example_graph()
sync_node_states(us_c, [n.id for n in graph_c.get_all_nodes()])
ok, reason = can_complete_node(make_ri(graph_c, us_c), "node-a")
assert ok, reason
assert reason == ""
print("14. can_complete_node → (True, '') for root node")

# ── 15. can_complete_node: prerequisite not met ────────────────────────
ok, reason = can_complete_node(make_ri(graph_c, us_c), "node-b")
assert not ok
assert "Prerequisite not met" in reason
assert "node-a" in reason
print(f"15. can_complete_node blocked: {reason}")

# ── 16. can_complete_node: already completed ───────────────────────────
complete_node(us_c, "node-a")
ok, reason = can_complete_node(make_ri(graph_c, us_c), "node-a")
assert not ok
assert "already" in reason.lower()
print(f"16. can_complete_node → already completed: {reason}")

# ── 17. can_complete_node: unknown node ────────────────────────────────
ok, reason = can_complete_node(make_ri(graph_c, us_c), "no-such-node")
assert not ok
assert "Unknown node" in reason
print(f"17. can_complete_node → unknown node: {reason}")

# ── 18. Determinism: same inputs → same outputs ────────────────────────
graph_d, us_d = load_example_graph()
sync_node_states(us_d, [n.id for n in graph_d.get_all_nodes()])
r1 = compute_availability(make_ri(graph_d, us_d))
r2 = compute_availability(make_ri(graph_d, us_d))
assert r1 == r2
print("18. Determinism: identical results from identical inputs")

# ── 19. Resolver imports (AST analysis) ────────────────────────────────
resolver_path = os.path.join("runtime", "los", "engine", "resolver.py")
with open(resolver_path, encoding="utf-8") as f:
    tree = ast.parse(f.read())

imports: set[str] = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for alias in node.names:
            imports.add(alias.name.split(".")[0])
    elif isinstance(node, ast.ImportFrom):
        if node.module:
            imports.add(node.module.split(".")[0])

forbidden = {"storage", "cli", "main", "los.state.models"}
found_forbidden = set()
for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom) and node.module:
        for f in forbidden:
            if node.module == f or node.module.startswith(f + "."):
                found_forbidden.add(node.module)

assert not found_forbidden, f"Forbidden imports found: {found_forbidden}"
assert "los" in imports, f"Expected 'los' in imports, got: {imports}"
print(f"19. AST import check OK (imports: {sorted(imports)}), no forbidden: {forbidden}")

# ── 20. can_complete_node does not modify UserState ────────────────────
graph_v, us_v = load_example_graph()
sync_node_states(us_v, [n.id for n in graph_v.get_all_nodes()])
history_before = len(us_v.history)
status_before = us_v.node_states["node-a"].status
ok, _ = can_complete_node(make_ri(graph_v, us_v), "node-a")
assert ok
assert len(us_v.history) == history_before
assert us_v.node_states["node-a"].status == status_before  # NOT_STARTED still
print("20. can_complete_node does NOT mutate UserState")

print()
print("All tests passed.")
