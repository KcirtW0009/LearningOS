"""Shared test utilities for Learning OS test suite.

Provides common fixtures to reduce duplication across test files:
  - make_temp_graph()    — create an in-memory graph from node/edge lists
  - load_example_graph() — load example-basics with fresh UserState
  - fresh_state()        — sync all graph nodes into a new UserState
  - cleanup_state_file() — remove persisted state between tests
"""

from __future__ import annotations

import os
import tempfile

import yaml

# Ensure the runtime package is on sys.path for all test files
import sys as _sys

_RUNTIME_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "runtime")
)
if _RUNTIME_PATH not in _sys.path:
    _sys.path.insert(0, _RUNTIME_PATH)


# ── Graph construction ──────────────────────────────────────────────────


def make_temp_graph(
    nodes: list[dict],
    edges: list[dict],
    package_id: str = "test",
    name: str = "Test",
    version: str = "1.0.0",
) -> str:
    """Create a temporary Graph Package and return its path.

    *nodes* and *edges* are lists of dicts conforming to the LOS-0305
    single-file schema.  The caller is responsible for cleanup.
    """
    td = tempfile.mkdtemp()
    with open(os.path.join(td, "manifest.yaml"), "w", encoding="utf-8") as f:
        yaml.dump(
            {"package_id": package_id, "name": name, "version": version}, f
        )
    with open(os.path.join(td, "graph.yaml"), "w", encoding="utf-8") as f:
        yaml.dump({"nodes": nodes, "edges": edges}, f)
    return td


# ── State helpers ───────────────────────────────────────────────────────


def fresh_state(graph) -> "UserState":
    """Return a new UserState with all *graph* nodes synced at NOT_STARTED."""
    from los.state.engine import sync_node_states
    from los.state.models import UserState

    us = UserState(graph_id=graph.package_id, graph_version=graph.package_version)
    sync_node_states(us, [n.id for n in graph.get_all_nodes()])
    return us


def load_example_graph() -> "tuple[LoadedGraph, UserState]":
    """Load ``graphs/example-basics`` with a fresh UserState."""
    from los.graph.loader import load_graph_package

    graph = load_graph_package("graphs/example-basics")
    us = fresh_state(graph)
    return graph, us


# ── Persistence helpers ─────────────────────────────────────────────────


def cleanup_state_file() -> None:
    """Remove all persisted state files from the data/ directory."""
    import glob
    import los.storage.adapter as _sada

    data_dir = os.path.join(os.getcwd(), "data")
    if os.path.isdir(data_dir):
        # Remove per-graph state files
        for pattern in ["user-state*.json", _sada.DEFAULT_MANIFEST_PATH]:
            full_pattern = os.path.join(data_dir, pattern)
            for f in glob.glob(full_pattern):
                os.remove(f)
