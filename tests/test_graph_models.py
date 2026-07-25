"""test_graph_models — Node and Edge dataclass validation."""
import sys
sys.path.insert(0, ".")

from dataclasses import FrozenInstanceError

from los.graph.models import Node, Edge, VALID_RELATIONS, is_blocking_relation


print("=== test_graph_models ===")
print()

# ── 1. Node: valid construction ─────────────────────────────────────
n = Node(id="test-node", title="Test Node", description="A test node")
assert n.id == "test-node"
assert n.title == "Test Node"
assert n.description == "A test node"
assert n.type is None
assert n.difficulty is None
print("1. Node construction OK")

# ── 2. Node: optional fields ────────────────────────────────────────
n2 = Node(
    id="advanced-node",
    title="Advanced",
    description="Advanced node",
    type="skill",
    difficulty="advanced",
)
assert n2.type == "skill"
assert n2.difficulty == "advanced"
print("2. Node optional fields OK")

# ── 3. Node: reject empty id ────────────────────────────────────────
try:
    Node(id="", title="T", description="D")
    assert False, "should have raised"
except ValueError as e:
    assert "id" in str(e)
print("3. Reject empty Node.id OK")

# ── 4. Node: reject whitespace-only id ──────────────────────────────
try:
    Node(id="   ", title="T", description="D")
    assert False, "should have raised"
except ValueError as e:
    assert "id" in str(e)
print("4. Reject whitespace Node.id OK")

# ── 5. Node: reject empty title ─────────────────────────────────────
try:
    Node(id="n1", title="", description="D")
    assert False
except ValueError as e:
    assert "title" in str(e)
print("5. Reject empty Node.title OK")

# ── 6. Node: reject empty description ───────────────────────────────
try:
    Node(id="n2", title="T", description="")
    assert False
except ValueError as e:
    assert "description" in str(e)
print("6. Reject empty Node.description OK")

# ── 7. Node: frozen (immutable) ─────────────────────────────────────
try:
    n.id = "mutated"
    assert False, "should have raised"
except FrozenInstanceError:
    pass
print("7. Node frozen (immutable) OK")

# ── 8. Edge: valid construction ─────────────────────────────────────
e = Edge(source="a", target="b", relation="prerequisite")
assert e.source == "a"
assert e.target == "b"
assert e.relation == "prerequisite"
print("8. Edge construction OK")

# ── 9. Edge: reject empty source ────────────────────────────────────
try:
    Edge(source="", target="b", relation="r")
    assert False
except ValueError as ve:
    assert "source" in str(ve)
print("9. Reject empty Edge.source OK")

# ── 10. Edge: reject empty target ───────────────────────────────────
try:
    Edge(source="a", target="", relation="r")
    assert False
except ValueError as ve:
    assert "target" in str(ve)
print("10. Reject empty Edge.target OK")

# ── 11. Edge: reject empty relation ─────────────────────────────────
try:
    Edge(source="a", target="b", relation="")
    assert False
except ValueError as ve:
    assert "relation" in str(ve)
print("11. Reject empty Edge.relation OK")

# ── 12. Edge: frozen (immutable) ────────────────────────────────────
try:
    e.source = "mutated"
    assert False
except FrozenInstanceError:
    pass
print("12. Edge frozen (immutable) OK")

# ── 13. VALID_RELATIONS: well-known types ───────────────────────────
assert "prerequisite" in VALID_RELATIONS
assert "dependency" in VALID_RELATIONS
assert "progression" in VALID_RELATIONS
assert "association" in VALID_RELATIONS
assert "alternative" in VALID_RELATIONS
assert len(VALID_RELATIONS) == 5
print("13. VALID_RELATIONS contains 5 known types OK")

# ── 14. is_blocking_relation ────────────────────────────────────────
assert is_blocking_relation("prerequisite")
assert is_blocking_relation("dependency")
assert is_blocking_relation("progression")
assert not is_blocking_relation("association")
assert not is_blocking_relation("alternative")
print("14. is_blocking_relation OK")

# ── 15. Node: equality ──────────────────────────────────────────────
n_a = Node(id="eq", title="A", description="D")
n_b = Node(id="eq", title="A", description="D")
assert n_a == n_b
print("15. Node equality OK")

# ── 16. Edge: equality ──────────────────────────────────────────────
e_a = Edge(source="x", target="y", relation="prerequisite")
e_b = Edge(source="x", target="y", relation="prerequisite")
assert e_a == e_b
print("16. Edge equality OK")

print()
print("All tests passed.")
