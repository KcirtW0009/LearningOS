"""ResolutionInput capability contract.

Consumer: Resolver (los.engine.resolver)
Providers: State Authority + Graph layer

What this IS:
  The minimum capability boundary for the Resolver to compute
  availability and validate completion eligibility, without
  importing State Authority's or Graph layer's internal data models.

What this IS NOT:
  A replacement for UserState, LoadedGraph, Node, or Edge.
  Those remain the internal models of their respective authorities.

Derived from:
  RS-005 Runtime Resolver Interface (Frozen)
  Implementation Mapping §7.2 Resolver to State (Frozen)
  CT-003 ResolutionInputContract Implementation
"""

from __future__ import annotations

from typing import Protocol

from los.runtime.contracts.state_access import StateReader


# ── GraphReader Protocol ───────────────────────────────────────────


class GraphReader(Protocol):
    """Read-only graph capability contract.

    Satisfied by: ``los.graph.loader.LoadedGraph`` (after CT-003
    method additions).
    """

    def get_node_ids(self) -> list[str]:
        """Return all node IDs in insertion order."""
        ...

    def node_exists(self, node_id: str) -> bool:
        """Return True if *node_id* exists in the graph."""
        ...

    def get_blocking_source_ids(self, node_id: str) -> list[str]:
        """Return source IDs of all incoming blocking edges for *node_id*.

        Blocking edges are those whose relation type is considered
        a prerequisite barrier (prerequisite, dependency, progression).
        """
        ...


# ── ResolutionInput Protocol ──────────────────────────────────────


class ResolutionInput(StateReader, GraphReader, Protocol):
    """Combined capability contract for the Resolver.

    The Resolver requires both graph structure queries and learning
    state queries to compute availability.  This contract composes
    both capabilities without exposing internal models.
    """
