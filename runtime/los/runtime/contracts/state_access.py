"""StateAccess capability contracts.

Consumer: Runtime Authority
Provider: State Authority (los.state.engine + los.state.models)

What this IS:
  The minimum capability boundary for Runtime to read learning state and
  request state mutations, without importing State Authority's internal
  data model directly.

What this IS NOT:
  A replacement for UserState.
  UserState remains the internal model of State Authority.
  These contracts define the EXTERNAL capability boundary.

Derived from:
  RS-004 State Access Contract (Frozen)
  Implementation Mapping §8.1 Runtime to State (Frozen)
  CPR-004 StateAccessContract Boundary Design (Approved)
  CT-001-PATCH Complete StateAccessContract Surface
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


# ── Value Objects ──────────────────────────────────────────────────


@dataclass(frozen=True)
class ProgressSnapshot:
    """Immutable progress summary returned by StateReader.get_progress()."""

    total: int
    completed: int
    mastered: int
    percentage: float


@dataclass(frozen=True)
class MutationResult:
    """Immutable result returned by StateMutator operations."""

    success: bool
    node_id: str
    message: str


# ── StateReader Protocol ───────────────────────────────────────────


class StateReader(Protocol):
    """Read-only capability contract for learning state queries.

    Satisfied by: ``los.state.models.UserState`` (future — semantic
    query methods to be added to the state model).
    """

    def is_tracked(self, node_id: str) -> bool:
        """Return True if *node_id* has a state entry."""
        ...

    def is_completed(self, node_id: str) -> bool:
        """Return True if *node_id* is COMPLETED or MASTERED."""
        ...

    def get_status(self, node_id: str) -> str:
        """Return the status string for *node_id*.

        Returns 'NOT_STARTED' if the node is not tracked.
        """
        ...

    def get_score(self, node_id: str) -> int:
        """Return the score for *node_id*, or 0 if not tracked."""
        ...

    def get_evidence(self, node_id: str) -> list[str]:
        """Return evidence references for *node_id*.

        Returns an empty list if the node is not tracked.
        """
        ...

    def get_progress(self) -> ProgressSnapshot:
        """Return an immutable progress summary."""
        ...


# ── StateMutator Protocol ──────────────────────────────────────────


class StateMutator(Protocol):
    """Mutation capability contract for learning state transitions.

    Satisfied by: ``los.state.engine`` functions (future — method-form
    adapter to be introduced on the state handle).
    """

    def complete_node(
        self, node_id: str, score: int, evidence: list[str]
    ) -> MutationResult:
        """Mark *node_id* as COMPLETED with the given score and evidence.

        Returns a MutationResult indicating success or failure reason.
        """
        ...

    def start_node(self, node_id: str) -> MutationResult:
        """Mark *node_id* as IN_PROGRESS.

        Returns a MutationResult indicating success or failure reason.
        """
        ...


# ── Combined Contract (backward-compatible alias) ──────────────────


class StateAccess(StateReader, StateMutator):
    """Combined read + mutate capability contract.

    Maintained for backward compatibility with existing consumers
    that use a single state handle.  New consumers should import
    ``StateReader`` or ``StateMutator`` directly.
    """
