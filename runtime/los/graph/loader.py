"""Graph Package loader.

Defined by:
  - LOS-0202 Graph Loader
  - LOS-0305 Graph Package Schema
  - LOS-0403 Graph Engine (loading process)

Reads manifest.yaml + graph.yaml → builds LoadedGraph.
"""

from __future__ import annotations

import os
from typing import Any

import yaml

from los.exceptions import (
    GraphNotFoundError,
    GraphParseError,
    GraphValidationError,
)
from los.graph.models import VALID_RELATIONS, Edge, Node, Resource, is_blocking_relation
from los.graph.validator import validate_edges, validate_nodes


# ── LoadedGraph ───────────────────────────────────────────────────────


class LoadedGraph:
    """The in-memory representation of a loaded Graph Package (LOS-0403).

    Attributes:
        package_id    — from manifest.yaml
        package_name  — from manifest.yaml
        package_version — from manifest.yaml
        author        — optional, from manifest.yaml
        nodes         — ordered list of Node objects
        edges         — ordered list of Edge objects
        node_index    — dict of node_id → Node
        edges_by_source — dict of source_node_id → list[Edge]
    """

    def __init__(
        self,
        package_id: str,
        package_name: str,
        package_version: str,
        author: str,
        nodes: list[Node],
        edges: list[Edge],
    ) -> None:
        self.package_id = package_id
        self.package_name = package_name
        self.package_version = package_version
        self.author = author
        self.nodes = nodes
        self.edges = edges
        self.node_index: dict[str, Node] = {n.id: n for n in nodes}
        self.edges_by_source: dict[str, list[Edge]] = {}
        for e in edges:
            self.edges_by_source.setdefault(e.source, []).append(e)

    # ── queries (LOS-0403) ───────────────────────────────────────────

    def get_node(self, node_id: str) -> Node | None:
        """Return the Node with *node_id*, or None."""
        return self.node_index.get(node_id)

    def get_all_nodes(self) -> list[Node]:
        """Return every Node in insertion order."""
        return list(self.nodes)

    def get_edges_from(self, node_id: str) -> list[Edge]:
        """Return all Edges whose source is *node_id*."""
        return list(self.edges_by_source.get(node_id, []))

    def get_all_edges(self) -> list[Edge]:
        """Return every Edge in insertion order."""
        return list(self.edges)

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    # ── GraphReader contract (CT-003) ──────────────────────────────

    def get_node_ids(self) -> list[str]:
        """Return all node IDs in insertion order."""
        return [n.id for n in self.nodes]

    def node_exists(self, node_id: str) -> bool:
        """Return True if *node_id* exists in the graph."""
        return node_id in self.node_index

    def get_blocking_source_ids(self, node_id: str) -> list[str]:
        """Return source IDs of all incoming blocking edges for *node_id*."""
        sources: list[str] = []
        for edge in self.edges:
            if edge.target == node_id and is_blocking_relation(edge.relation):
                sources.append(edge.source)
        return sources


# ── Public API ────────────────────────────────────────────────────────


def load_graph_package(package_path: str) -> LoadedGraph:
    """Load and validate a Graph Package from *package_path*.

    Expects two files: ``manifest.yaml`` and ``graph.yaml``.

    Raises:
        GraphNotFoundError   — package_path, manifest.yaml, or graph.yaml missing
        GraphParseError      — malformed YAML or missing required fields
        GraphValidationError — graph structure validation failure
        yaml.YAMLError       — YAML parse error
    """
    if not os.path.isdir(package_path):
        raise GraphNotFoundError(f"Graph package path not found: {package_path}")

    manifest_path = os.path.join(package_path, "manifest.yaml")
    graph_path = os.path.join(package_path, "graph.yaml")

    if not os.path.isfile(manifest_path):
        raise GraphNotFoundError(
            f"manifest.yaml not found in package: {package_path}"
        )
    if not os.path.isfile(graph_path):
        raise GraphNotFoundError(
            f"graph.yaml not found in package: {package_path}"
        )

    # ── 1. Read & validate manifest ──────────────────────────────────
    manifest = _read_yaml(manifest_path)
    _validate_manifest(manifest)

    # ── 2. Read graph.yaml ───────────────────────────────────────────
    graph_raw = _read_yaml(graph_path)

    # ── 3. Parse Nodes ───────────────────────────────────────────────
    nodes = _parse_nodes(graph_raw)

    # ── 4. Parse Edges ───────────────────────────────────────────────
    edges = _parse_edges(graph_raw)

    # ── 5. Validate ──────────────────────────────────────────────────
    node_errors = validate_nodes(nodes)
    if node_errors:
        raise GraphValidationError("Graph validation failed:\n  " + "\n  ".join(node_errors))

    node_ids = {n.id for n in nodes}
    edge_errors = validate_edges(edges, node_ids)
    if edge_errors:
        raise GraphValidationError("Graph validation failed:\n  " + "\n  ".join(edge_errors))

    # ── 6. Build LoadedGraph ─────────────────────────────────────────
    return LoadedGraph(
        package_id=manifest["package_id"],
        package_name=manifest["name"],
        package_version=manifest["version"],
        author=manifest.get("author", ""),
        nodes=nodes,
        edges=edges,
    )


# ── internal helpers ──────────────────────────────────────────────────


def _read_yaml(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        raise GraphParseError(f"Empty YAML file: {path}")
    return data


def _validate_manifest(m: dict[str, Any]) -> None:
    required = ["package_id", "name", "version"]
    for field in required:
        if field not in m or not str(m[field]).strip():
            raise GraphParseError(
                f"Missing required field '{field}' in manifest.yaml"
            )


def _parse_nodes(raw: dict[str, Any]) -> list[Node]:
    raw_nodes: list[dict[str, Any]] = raw.get("nodes", [])
    if not isinstance(raw_nodes, list):
        raise GraphParseError("'nodes' in graph.yaml must be a list")

    nodes: list[Node] = []
    for i, item in enumerate(raw_nodes):
        if not isinstance(item, dict):
            raise GraphParseError(f"Node at index {i}: must be a mapping")

        # Required fields
        for field in ("id", "title", "description"):
            if field not in item or not str(item[field]).strip():
                raise GraphParseError(
                    f"Missing required field '{field}' for Node at index {i}"
                )

        nodes.append(
            Node(
                id=item["id"],
                title=item["title"],
                description=item["description"],
                type=item.get("type"),
                difficulty=item.get("difficulty"),
                resources=_parse_resources(item.get("resources", [])),
            )
        )
    return nodes


def _parse_edges(raw: dict[str, Any]) -> list[Edge]:
    raw_edges: list[dict[str, Any]] = raw.get("edges", [])
    if not isinstance(raw_edges, list):
        raise GraphParseError("'edges' in graph.yaml must be a list")

    edges: list[Edge] = []
    for i, item in enumerate(raw_edges):
        if not isinstance(item, dict):
            raise GraphParseError(f"Edge at index {i}: must be a mapping")

        # YAML 'from' → Python 'source' (reserved keyword)
        if "from" not in item:
            raise GraphParseError(f"Missing required field 'from' for Edge at index {i}")
        if "to" not in item:
            raise GraphParseError(f"Missing required field 'to' for Edge at index {i}")
        relation = item.get("relation", "")
        if not relation or not str(relation).strip():
            raise GraphParseError(
                f"Missing required field 'relation' for Edge at index {i}"
            )

        # LOS-0305: reject unknown relation types
        if relation not in VALID_RELATIONS:
            raise GraphParseError(
                f"Unknown relation type '{relation}' for Edge at index {i}. "
                f"Must be one of: {', '.join(sorted(VALID_RELATIONS))}"
            )

        edges.append(
            Edge(
                source=item["from"],
                target=item["to"],
                relation=relation,
            )
        )
    return edges


def _parse_resources(raw: list[dict[str, Any]]) -> list[Resource]:
    """Parse resource entries from a Node's YAML resources list."""
    if not isinstance(raw, list):
        raise GraphParseError("Node 'resources' must be a list")
    result: list[Resource] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise GraphParseError(f"Resource at index {i}: must be a mapping")
        if "type" not in item or not str(item["type"]).strip():
            raise GraphParseError(
                f"Resource at index {i}: missing required field 'type'"
            )
        if "uri" not in item or not str(item["uri"]).strip():
            raise GraphParseError(
                f"Resource at index {i}: missing required field 'uri'"
            )
        result.append(Resource(
            type=item["type"],
            uri=item["uri"],
            label=item.get("label"),
        ))
    return result
