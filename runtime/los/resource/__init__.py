"""ResourceIndex — simple resource query for loaded Graphs.

Defined by: RES-002 Resource Index (Phase 6)

Responsibilities:
  - Query resources by node_id from a LoadedGraph
  - Filter resources by type
  - Stateless read-only queries

Does NOT own:
  - Resource creation (Graph owns this)
  - Persistence
  - Runtime selection
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from los.graph.models import Resource

if TYPE_CHECKING:
    from los.graph.loader import LoadedGraph


def get_resources(graph: LoadedGraph, node_id: str) -> list[Resource]:
    """Return all resources for *node_id*, or empty list if node not found."""
    node = graph.get_node(node_id)
    if node is None:
        return []
    return list(node.resources)


def get_resources_by_type(
    graph: LoadedGraph, node_id: str, resource_type: str
) -> list[Resource]:
    """Return resources of a specific type for *node_id*."""
    return [r for r in get_resources(graph, node_id) if r.type == resource_type]
