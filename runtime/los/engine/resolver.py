"""Runtime Engine Resolver — availability calculation and completion validation.

Defined by:
  - LOS-0403 Graph Engine (Find Available Nodes)
  - LOS-0404 State Engine (Available Node Calculation)
  - LOS-0500 Phase 7 Runtime Engine
  - Phase 7 Design Review (approved)
  - Phase 2 RuntimeInstance Migration

The Resolver is the orchestration layer that combines Graph structure
(what can be learned) with learning state (what has been done) to produce
derived runtime statuses.

Pure functions — deterministic, no side effects, no state mutation.

ResolutionContext (CT-003 adapter) removed in Phase 2.
RuntimeInstance now structurally satisfies ResolutionInput directly.
"""

from __future__ import annotations

from los.engine.contracts.input import ResolutionInput


# ── Public API ─────────────────────────────────────────────────────────


def compute_availability(
    context: ResolutionInput,
) -> dict[str, str]:
    """Compute derived runtime status for every Node in the graph.

    Returns a dict mapping ``node_id`` to one of:

    * ``"LOCKED"``      — at least one blocking prerequisite is incomplete
    * ``"AVAILABLE"``   — all blocking prerequisites satisfied; node not started
    * ``"IN_PROGRESS"`` — user has started (stored status)
    * ``"COMPLETED"``   — user has completed (stored status)
    * ``"MASTERED"``    — user has mastered (stored status)

    Pure function.  Deterministic: same inputs → same outputs.
    """
    result: dict[str, str] = {}
    for nid in context.get_node_ids():
        status = context.get_status(nid)

        # Pass through stored non-initial statuses
        if status != "NOT_STARTED":
            result[nid] = status
            continue

        # Check blocking incoming edges
        blockers = context.get_blocking_source_ids(nid)

        if not blockers:
            result[nid] = "AVAILABLE"  # root node
        else:
            all_satisfied = all(
                context.is_completed(src) for src in blockers
            )
            result[nid] = "AVAILABLE" if all_satisfied else "LOCKED"

    return result


def get_available_nodes(
    context: ResolutionInput,
) -> list[str]:
    """Return IDs of all AVAILABLE Nodes, in insertion order."""
    statuses = compute_availability(context)
    return [
        nid
        for nid in context.get_node_ids()
        if statuses.get(nid) == "AVAILABLE"
    ]


def can_complete_node(
    context: ResolutionInput,
    node_id: str,
) -> tuple[bool, str]:
    """Check whether *node_id* is eligible for completion.

    Validates:
      1. Node exists in Graph.
      2. Node is not already COMPLETED or MASTERED.
      3. All blocking prerequisites are satisfied.

    Returns ``(True, "")`` or ``(False, reason)``.

    Does NOT modify state, write storage, or call complete_node().
    """
    # 1. Node existence (graph-level, via contract)
    if not context.node_exists(node_id):
        return False, f"Unknown node: '{node_id}'"

    # 2. Current completion state (state-level, via contract)
    if context.is_completed(node_id):
        return False, f"Node '{node_id}' is already {context.get_status(node_id)}"

    # 3. Blocking prerequisites (graph + state, via contract)
    for src in context.get_blocking_source_ids(node_id):
        if not context.is_completed(src):
            return False, f"Prerequisite not met: '{src}'"

    return True, ""
