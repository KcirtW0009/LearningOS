"""Graph structure validator.

Defined by:
  - LOS-0305 Graph Package Schema
  - LOS-0403 Graph Engine (validation section)

Validates:
  - Node ID uniqueness
  - Edge references (source and target must exist)
  - Required fields presence
"""

from __future__ import annotations

from typing import Sequence

from los.graph.models import Edge, Node, VALID_RELATIONS

def validate_nodes(nodes: Sequence[Node]) -> list[str]:
    """Validate a sequence of Nodes.

    Returns a list of error strings (empty list = valid).
    """
    errors: list[str] = []
    seen_ids: set[str] = set()

    for i, node in enumerate(nodes):
        if not node.id or not node.id.strip():
            errors.append(f"Node at index {i}: missing or empty 'id'")
            continue
        if node.id in seen_ids:
            errors.append(f"Duplicate Node ID: '{node.id}'")
        seen_ids.add(node.id)

        if not node.title or not node.title.strip():
            errors.append(f"Node '{node.id}': missing or empty 'title'")
        if not node.description or not node.description.strip():
            errors.append(f"Node '{node.id}': missing or empty 'description'")

    return errors


def validate_edges(edges: Sequence[Edge], node_ids: set[str]) -> list[str]:
    """Validate a sequence of Edges against a known set of *node_ids*.

    Returns a list of error strings (empty list = valid).
    """
    errors: list[str] = []
    seen_edges: set[tuple[str, str, str]] = set()

    for i, edge in enumerate(edges):
        if edge.relation not in VALID_RELATIONS:
            errors.append(
                f"Edge at index {i}: unknown relation '{edge.relation}'. "
                f"Must be one of: {', '.join(sorted(VALID_RELATIONS))}"
            )
        if edge.source not in node_ids:
            errors.append(
                f"Edge at index {i}: 'from' references unknown Node '{edge.source}'"
            )
        if edge.target not in node_ids:
            errors.append(
                f"Edge at index {i}: 'to' references unknown Node '{edge.target}'"
            )

        key = (edge.source, edge.target, edge.relation)
        if key in seen_edges:
            errors.append(
                f"Duplicate Edge: {edge.source} --[{edge.relation}]--> {edge.target}"
            )
        seen_edges.add(key)

    return errors
