"""test_graph_validator — Graph structure validation (validate_nodes, validate_edges)."""
import sys
sys.path.insert(0, ".")

from los.graph.models import Node, Edge
from los.graph.validator import validate_nodes, validate_edges


print("=== test_graph_validator ===")
print()

# ── 1. Valid graph passes validation ────────────────────────────────
nodes = [
    Node(id="a", title="A", description="Node A"),
    Node(id="b", title="B", description="Node B"),
]
edges = [
    Edge(source="a", target="b", relation="prerequisite"),
]
node_errors = validate_nodes(nodes)
assert node_errors == [], f"Expected no errors, got: {node_errors}"

node_ids = {n.id for n in nodes}
edge_errors = validate_edges(edges, node_ids)
assert edge_errors == [], f"Expected no errors, got: {edge_errors}"
print("1. Valid graph passes OK")

# ── 2. Duplicate Node ID is rejected ────────────────────────────────
dup_nodes = [
    Node(id="dup", title="First", description="Desc"),
    Node(id="dup", title="Second", description="Another"),
]
errs = validate_nodes(dup_nodes)
assert len(errs) == 1
assert "Duplicate" in errs[0]
print(f"2. Duplicate Node ID rejected: {errs[0]}")

# ── 3. Edge: unknown source Node ────────────────────────────────────
src_edges = [
    Edge(source="no-such", target="a", relation="prerequisite"),
]
errs = validate_edges(src_edges, {"a"})
assert len(errs) == 1
assert "unknown Node 'no-such'" in errs[0]
print(f"3. Unknown source Node rejected: {errs[0]}")

# ── 4. Edge: unknown target Node ────────────────────────────────────
tgt_edges = [
    Edge(source="a", target="no-such", relation="prerequisite"),
]
errs = validate_edges(tgt_edges, {"a"})
assert len(errs) == 1
assert "unknown Node 'no-such'" in errs[0]
print(f"4. Unknown target Node rejected: {errs[0]}")

# ── 5. Duplicate Edge is rejected ───────────────────────────────────
dup_edge_nodes = [
    Node(id="x", title="X", description="Desc"),
    Node(id="y", title="Y", description="Desc"),
]
dup_edges = [
    Edge(source="x", target="y", relation="prerequisite"),
    Edge(source="x", target="y", relation="prerequisite"),
]
errs = validate_edges(dup_edges, {"x", "y"})
assert len(errs) == 1
assert "Duplicate Edge" in errs[0]
print(f"5. Duplicate Edge rejected: {errs[0]}")

# ── 6. Empty lists pass validation ──────────────────────────────────
errs = validate_nodes([])
assert errs == []
errs = validate_edges([], set())
assert errs == []
print("6. Empty lists pass validation OK")

# ── 7. Multiple errors returned ─────────────────────────────────────
# Note: Empty/missing required fields are caught by model __post_init__ (ValueError).
# Validator tests focus on structural errors (duplicate IDs, unknown references).
multi_nodes = [
    Node(id="dup", title="First", description="Desc"),
    Node(id="dup", title="Second", description="Desc"),
    Node(id="bad-ref", title="Bad Ref", description="Desc"),
]
multi_edges = [
    Edge(source="dup", target="no-such", relation="prerequisite"),
]
errs_nodes = validate_nodes(multi_nodes)
errs_edges = validate_edges(multi_edges, {n.id for n in multi_nodes})
assert len(errs_nodes) == 1  # one duplicate
assert len(errs_edges) == 1  # one unknown ref
print(f"7. Multiple errors returned (nodes={len(errs_nodes)}, edges={len(errs_edges)}) OK")

print()
print("All tests passed.")
