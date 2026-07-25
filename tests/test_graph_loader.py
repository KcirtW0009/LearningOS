"""test_graph_loader — Graph Package loading and validation."""
import sys
sys.path.insert(0, ".")

import os
import tempfile

import yaml

from tests.utils import make_temp_graph

from los.exceptions import (
    GraphNotFoundError, GraphParseError, GraphValidationError,
)
from los.graph.loader import load_graph_package


print("=== test_graph_loader ===")
print()

EXAMPLES = os.path.join("graphs", "example-basics")

# ── 1. Valid package (example-basics) loads successfully ─────────────
g = load_graph_package(EXAMPLES)
assert g.package_id == "example-basics"
assert g.package_name == "Example Basics"
assert g.package_version == "1.0.0"
assert len(g.get_all_nodes()) == 3
assert len(g.get_all_edges()) == 2
print(f"1. Loaded {g.package_id} v{g.package_version}: "
      f"{len(g.get_all_nodes())} nodes, {len(g.get_all_edges())} edges OK")

# ── 2. Missing package path ─────────────────────────────────────────
try:
    load_graph_package("graphs/no-such-package")
    assert False, "should have raised"
except GraphNotFoundError as e:
    assert "not found" in str(e)
print("2. Missing package path rejected: GraphNotFoundError")

# ── 3. Missing manifest.yaml ────────────────────────────────────────
td = tempfile.mkdtemp()
graph_path = os.path.join(td, "graph.yaml")
yaml.dump({"nodes": [], "edges": []}, open(graph_path, "w"))
try:
    load_graph_package(td)
    assert False
except GraphNotFoundError as e:
    assert "manifest.yaml" in str(e)
print("3. Missing manifest.yaml rejected: GraphNotFoundError")

# ── 4. Missing graph.yaml ───────────────────────────────────────────
td2 = tempfile.mkdtemp()
yaml.dump(
    {"package_id": "test", "name": "Test", "version": "1.0"},
    open(os.path.join(td2, "manifest.yaml"), "w"),
)
try:
    load_graph_package(td2)
    assert False
except GraphNotFoundError as e:
    assert "graph.yaml" in str(e)
print("4. Missing graph.yaml rejected: GraphNotFoundError")

# ── 5. Missing required Node fields ─────────────────────────────────
td3 = make_temp_graph(
    nodes=[
        {"id": "ok", "title": "OK", "description": "Fine"},
        {"id": "bad", "title": "", "description": "No title"},
    ],
    edges=[],
)
try:
    load_graph_package(td3)
    assert False
except GraphParseError as e:
    assert "title" in str(e).lower()
print("5. Missing Node title rejected: GraphParseError")

# ── 6. Empty YAML file is rejected ──────────────────────────────────
td4 = make_temp_graph(nodes=[], edges=[])
empty_graph = os.path.join(td4, "graph.yaml")
with open(empty_graph, "w") as f:
    f.write("")
try:
    load_graph_package(td4)
    assert False
except GraphParseError as e:
    assert "Empty" in str(e)
print("6. Empty graph.yaml rejected: GraphParseError")

# ── 7. Malformed YAML is rejected ───────────────────────────────────
td5 = make_temp_graph(nodes=[], edges=[])
bad_graph = os.path.join(td5, "graph.yaml")
with open(bad_graph, "w") as f:
    f.write("nodes: [unclosed: [")
try:
    load_graph_package(td5)
    assert False
except yaml.YAMLError:
    pass
print("7. Malformed YAML rejected OK")

# ── 8. Duplicate Node IDs rejected ──────────────────────────────────
td6 = make_temp_graph(
    nodes=[
        {"id": "dup", "title": "A", "description": "First"},
        {"id": "dup", "title": "B", "description": "Second"},
    ],
    edges=[],
)
try:
    load_graph_package(td6)
    assert False
except GraphValidationError as e:
    assert "Duplicate" in str(e)
print("8. Duplicate Node IDs rejected: GraphValidationError")

# ── 9. Edge referencing unknown Node ────────────────────────────────
td7 = make_temp_graph(
    nodes=[{"id": "a", "title": "A", "description": "Desc"}],
    edges=[{"from": "a", "to": "no-such", "relation": "prerequisite"}],
)
try:
    load_graph_package(td7)
    assert False
except GraphValidationError as e:
    assert "unknown" in str(e).lower()
print("9. Edge references unknown Node: GraphValidationError")

# ── 10. Unknown relation type rejected ──────────────────────────────
td8 = make_temp_graph(
    nodes=[{"id": "a", "title": "A", "description": "D"},
           {"id": "b", "title": "B", "description": "D"}],
    edges=[{"from": "a", "to": "b", "relation": "nonsense"}],
)
try:
    load_graph_package(td8)
    assert False
except GraphParseError as e:
    assert "Unknown relation type" in str(e)
print("10. Unknown relation type rejected: GraphParseError")

print()
print("All tests passed.")
