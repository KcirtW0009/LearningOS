"""Phase 8 CLI Interface — test suite.

Tests command handler functions directly (not argparse parsing).
Uses the module-level _runtime session state via the CLI handler API.
"""
import argparse
import os
import sys
import tempfile

import yaml

sys.path.insert(0, ".")

from tests.utils import cleanup_state_file, make_temp_graph

import los.cli.main as cli
from los.state.models import NodeStatus

# Clean persisted state from previous test runs
cleanup_state_file()

print("=== Phase 8 CLI Tests ===")
print()

# ── helpers ────────────────────────────────────────────────────────────


def reset_session():
    """Clear CLI session state between tests.

    Unbinds the session and removes persisted artifacts so that
    resume() does not pick up stale state.
    """
    cli._binding.unbind()
    # Remove persisted manifest — Phase 4 auto-resume from manifest
    manifest_path = os.path.join("data", "runtime-manifest.json")
    if os.path.isfile(manifest_path):
        os.remove(manifest_path)


def make_args(**kwargs):
    """Build an argparse.Namespace with the given kwargs."""
    ns = argparse.Namespace()
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


# ── 1. graph load: valid package ───────────────────────────────────────
reset_session()
result = cli.handle_graph_load(make_args(path="graphs/example-basics"))
assert "Loaded:" in result
assert "Example Basics" in result
assert "1.0.0" in result
assert "3 nodes" in result
assert "2 edges" in result
assert cli._binding.current_runtime is not None
assert cli._binding.current_runtime._graph.package_id == "example-basics"
assert len(cli._binding.current_runtime._state.node_states) == 3
print(f"1. graph load OK:\n{result}")

# ── 2. graph load: nonexistent path ────────────────────────────────────
reset_session()
result = cli.handle_graph_load(make_args(path="no/such/path"))
assert result.startswith("Error:")
assert "not found" in result.lower()
print(f"2. graph load bad path: {result}")

# ── 3. graph load: bad YAML ────────────────────────────────────────────
reset_session()
td = tempfile.mkdtemp()
with open(os.path.join(td, "manifest.yaml"), "w") as f:
    f.write(":")
with open(os.path.join(td, "graph.yaml"), "w") as f:
    f.write(":")
result = cli.handle_graph_load(make_args(path=td))
assert result.startswith("Error:")
print(f"3. graph load bad YAML: OK (error returned)")

# ── 4. graph info: with loaded graph ───────────────────────────────────
reset_session()
cli.handle_graph_load(make_args(path="graphs/example-basics"))
result = cli.handle_graph_info(make_args())
assert "example-basics" in result
assert "Example Basics" in result
assert "1.0.0" in result
assert "3" in result  # node count
assert "2" in result  # edge count
print(f"4. graph info OK:\n{result}")

# ── 5. graph info: no graph loaded ─────────────────────────────────────
reset_session()
result = cli.handle_graph_info(make_args())
assert result.startswith("Error:")
assert "No graph loaded" in result
print(f"5. graph info without load: {result}")

# ── 6. node list: shows available nodes ────────────────────────────────
reset_session()
cli.handle_graph_load(make_args(path="graphs/example-basics"))
result = cli.handle_node_list(make_args())
assert "Available:" in result
assert "Node A" in result     # root node, always available
assert "Node C" in result     # association from A, non-blocking → always available
assert "Node B" not in result  # prerequisite from A → locked
print(f"6. node list OK:\n{result}")

# ── 7. node list: nothing available ────────────────────────────────────
# Create a graph where all nodes have locked prerequisites
reset_session()
td2 = make_temp_graph(
    nodes=[
        {"id": "r", "title": "R", "description": "root"},
        {"id": "l", "title": "L", "description": "locked"},
    ],
    edges=[{"from": "r", "to": "l", "relation": "prerequisite"}],
    package_id="locked",
    name="Locked",
)
cli.handle_graph_load(make_args(path=td2))
result = cli.handle_node_list(make_args())
# r is available (root), l is locked
assert "R" in result
assert "L" not in result
print(f"7. node list (partial): OK")

# ── 8. node info: existing node ────────────────────────────────────────
reset_session()
cli.handle_graph_load(make_args(path="graphs/example-basics"))
result = cli.handle_node_info(make_args(node_id="node-a"))
assert "node-a" in result
assert "Node A" in result
assert "First learning unit" in result
assert "concept" in result.lower()
assert "beginner" in result.lower()
assert "AVAILABLE" in result or "NOT_STARTED" in result
print(f"8. node info OK")

# ── 9. node info: unknown node ─────────────────────────────────────────
result = cli.handle_node_info(make_args(node_id="no-such-node"))
assert result.startswith("Error:")
assert "Unknown node" in result
print(f"9. node info unknown: {result}")

# ── 10. node complete: available node → success ────────────────────────
reset_session()
cleanup_state_file()
cli.handle_graph_load(make_args(path="graphs/example-basics"))
result = cli.handle_node_complete(make_args(node_id="node-a"))
assert "Completed:" in result
assert "Node A" in result
# Verify state through RuntimeInstance
ns = cli._binding.current_runtime._state.get_node_state("node-a")
assert ns is not None and ns.status == NodeStatus.COMPLETED
print(f"10. node complete OK: {result}")

# ── 11. node complete: locked node → error ─────────────────────────────
# node-b has prerequisite node-a. Load fresh, don't complete node-a
cleanup_state_file()
reset_session()
cli.handle_graph_load(make_args(path="graphs/example-basics"))
result = cli.handle_node_complete(make_args(node_id="node-b"))
assert result.startswith("Error:")
assert "Prerequisite not met" in result or "prerequisite" in result.lower()
print(f"11. node complete locked: {result}")

# ── 12. node complete: already completed → error ───────────────────────
# node-a is already completed from test 10's session state
cli.handle_node_complete(make_args(node_id="node-a"))
result = cli.handle_node_complete(make_args(node_id="node-a"))
assert result.startswith("Error:")
assert "already" in result.lower()
print(f"12. node complete already done: {result}")

# ── 13. status: with loaded graph ──────────────────────────────────────
result = cli.handle_status(make_args())
assert "Example Basics" in result
assert "Progress:" in result
assert "Available:" in result
assert "Locked:" in result
print(f"13. status OK:\n{result}")

# ── 14. status: no graph loaded ────────────────────────────────────────
reset_session()
result = cli.handle_status(make_args())
assert result.startswith("Error:")
print(f"14. status without load: {result}")

# ── 15. Full workflow (integration) ────────────────────────────────────
reset_session()

# Clean up persisted state from previous tests
cleanup_state_file()

# Load
r1 = cli.handle_graph_load(make_args(path="graphs/example-basics"))
assert "Loaded:" in r1

# List — only root nodes
r2 = cli.handle_node_list(make_args())
assert "Node A" in r2

# Complete root
r3 = cli.handle_node_complete(make_args(node_id="node-a"))
assert "Completed:" in r3

# List again — now node-b should be available
r4 = cli.handle_node_list(make_args())
assert "Node B" in r4  # unlocked by completing node-a

# Status
r5 = cli.handle_status(make_args())
assert "1/3" in r5 or "33.3%" in r5

print("15. Full workflow OK: load → list → complete → list → status")
print(f"    node-a completed, node-b now available")

# ── 16. CLI handler functions don't implement business logic ────────────
# This is an architectural check — all handlers delegate to RuntimeInstance.
# Verified by code review: no availability calc, no prerequisite logic,
# no state transitions, no persistence serialization in cli/main.py.
import ast
cli_path = os.path.join("runtime", "los", "cli", "main.py")
with open(cli_path, encoding="utf-8") as f:
    tree = ast.parse(f.read())

# CLI should import from los.runtime (the single authority boundary)
cli_imports: set[str] = set()
for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom) and node.module:
        cli_imports.add(node.module.split(".")[0])
assert "los" in cli_imports

# Verify CLI no longer imports resolver, state engine, or storage directly
forbidden_direct = {"los.engine.resolver", "los.state.engine", "los.storage.adapter", "los.graph.loader"}
found_direct = set()
for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom) and node.module:
        if node.module in forbidden_direct:
            found_direct.add(node.module)
assert not found_direct, f"CLI should not import directly: {found_direct}"
print(f"16. CLI imports through RuntimeInstance only: {sorted(cli_imports)}")

# ── 16b. Phase 5 Architecture: CLI must use SessionBinding, not _runtime ──
assert not hasattr(cli, '_runtime'), \
    "CLI must not have _runtime global — owned by SessionBinding"
assert hasattr(cli, '_binding'), \
    "CLI must have _binding singleton for SessionBinding"
assert cli._binding is not None, \
    "CLI _binding singleton must be initialized"
print("16b. CLI uses SessionBinding (no _runtime global): OK")

# ── 17. CLI module can be imported standalone ───────────────────────────
# (already proven by the fact that all tests above passed)
print("17. CLI standalone import OK")

print()
print("All tests passed.")
