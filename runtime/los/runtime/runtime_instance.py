"""RuntimeInstance — Runtime Authority execution core.

Defined by:
  - RS-001 Runtime Graph Instance Model (Frozen)
  - RS-002 Runtime Lifecycle State Machine (Frozen)
  - RS-006 Runtime Authority Model (Frozen)
  - AD-003 Runtime Authority Ownership (Approved)
  - Phase 2 Implementation Contract (Accepted)

Responsibilities:
  - Graph binding and lifecycle orchestration
  - Delegation to Resolver (availability computation)
  - Delegation to State Engine (state mutation)
  - Delegation to Storage (persistence)
  - ResolutionInput satisfaction (structural — 9 one-liner delegation methods)

MUST NOT (Constraint 1):
  - Duplicate resolver logic
  - Duplicate graph validation logic
  - Duplicate state transition logic
  - Implement domain computation
  - Import UserState, NodeState, NodeStatus, or HistoryEntry directly

Principle: orchestration only, not domain computation.
"""

from __future__ import annotations

import uuid
from enum import Enum

import yaml

from los.common import utc_now_iso as _utc_now_iso
from los.engine.resolver import (
    can_complete_node,
    compute_availability,
    get_available_nodes,
)
from los.engine.xp import calculate_boss_bonus as _calculate_boss_bonus
from los.engine.xp import calculate_xp as _calculate_xp
from los.engine.xp import get_proficiency as _get_proficiency
from los.exceptions import InvalidStateTransitionError, LOSError, RecoveryError
from los.graph.loader import LoadedGraph, load_graph_package
from los.runtime.contracts.state_access import ProgressSnapshot, StateAccess
from los.runtime.runtime_manifest import (
    DEFAULT_MANIFEST_PATH,
    RuntimeManifest,
)
from los.state.engine import (
    StateHandle,
    get_progress as _state_get_progress,
    sync_node_states,
)
from los.state.models import UndoEntry
from los.storage.adapter import (
    DEFAULT_STATE_PATH,
    load as _storage_load,
    load_global_state as _storage_load_global,
    load_manifest as _storage_load_manifest,
    save as _storage_save,
    save_global_state as _storage_save_global,
    save_manifest as _storage_save_manifest,
    state_path_for_graph,
)


# ── Phase 7 XP integration helper ────────────────────────────────────


def _earn_xp(node, score: int, state) -> tuple[int, int]:
    """Calculate and accrue XP for completing *node* with *score*.

    Returns:
        (base_xp, boss_bonus) — total XP earned = base_xp + boss_bonus.
        boss_bonus is 0 for non-milestone nodes.
    """
    previous_score = state.get_score(node.id)
    xp = _calculate_xp(getattr(node, "difficulty", None), score, previous_score)
    bonus = 0
    node_type = getattr(node, "type", None)
    if node_type == "milestone":
        bonus = _calculate_boss_bonus(getattr(node, "difficulty", None))
    total = xp + bonus
    state.add_xp(total)
    return xp, bonus


# ── RuntimeStatus (RS-002) ──────────────────────────────────────────


class RuntimeStatus(str, Enum):
    """RS-002 5-state lifecycle.

    Phase 2 implements CREATED → ACTIVE only.
    VALIDATED and ACTIVATED are reserved for future extension points.
    RETIRED is reserved for lifecycle termination.
    """

    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    ACTIVATED = "ACTIVATED"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


# ── RuntimeInstance ─────────────────────────────────────────────────


class RuntimeInstance:
    """Runtime Authority execution core.

    Owns:
      - Graph binding (self._graph)
      - State handle (self._state)
      - Lifecycle coordination (_transition gate)
      - ResolutionInput delegation (9 one-liner methods)

    Does NOT implement domain computation — delegates to Resolver,
    State Engine, and Storage Adapter.

    Constructor:
        RuntimeInstance(graph, state)  — private; use load() or resume()

    Lifecycle:
        CREATED (constructor)
        → ACTIVE (via _transition, called by load()/resume())
    """

    def __init__(self, graph: LoadedGraph, state: StateAccess) -> None:
        """Create a RuntimeInstance in CREATED status.

        Args:
            graph: The loaded Graph Package binding.
            state:  A StateAccess-compatible handle (UserState at runtime).
                    Must NOT be typed or referred to as user_state.
        """
        self._runtime_id: str = uuid.uuid4().hex[:12]
        self._status: RuntimeStatus = RuntimeStatus.CREATED
        self._graph: LoadedGraph = graph
        self._state: StateAccess = state
        self._mutator: StateHandle = StateHandle(self._state)
        self._manifest: RuntimeManifest | None = None
        self._global_state = _storage_load_global()

    # ── lifecycle ──────────────────────────────────────────────────

    @property
    def status(self) -> RuntimeStatus:
        """Read-only lifecycle status. Never mutate directly."""
        return self._status

    @property
    def runtime_id(self) -> str:
        """Immutable runtime identity (RS-001)."""
        return self._runtime_id

    def _transition(self, new_status: RuntimeStatus) -> None:
        """Sole lifecycle mutation gate (Constraint 4).

        Raises:
            InvalidStateTransitionError: If the transition is not allowed.

        NEVER bypass — even in tests.  Use ``runtime.status`` to read.
        """
        valid_transitions: dict[RuntimeStatus, set[RuntimeStatus]] = {
            RuntimeStatus.CREATED: {RuntimeStatus.ACTIVE},
            # Future: VALIDATED, ACTIVATED extension points
            RuntimeStatus.ACTIVE: set(),
            RuntimeStatus.VALIDATED: set(),
            RuntimeStatus.ACTIVATED: set(),
            RuntimeStatus.RETIRED: set(),
        }
        allowed = valid_transitions.get(self._status, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                f"Cannot transition from {self._status.value} "
                f"to {new_status.value}"
            )
        self._status = new_status

    # ── factories (classmethods) ────────────────────────────────────

    @classmethod
    def load(cls, package_path: str) -> RuntimeInstance:
        """Load a Graph Package and create an active RuntimeInstance.

        Lifecycle: CREATED → ACTIVE.
        Creates and persists a RuntimeManifest alongside UserState.

        Raises:
            LOSError, yaml.YAMLError: Graph loading or validation failure.
        """
        graph = cls._load_graph(package_path)
        state = cls._initialize_state(graph, package_path)

        runtime = cls(graph=graph, state=state)
        runtime._manifest = RuntimeManifest(
            runtime_id=runtime._runtime_id,
            graph_path=package_path,
            graph_id=graph.package_id,
            graph_version=graph.package_version,
        )
        runtime._transition(RuntimeStatus.ACTIVE)
        runtime.save()

        return runtime

    @classmethod
    def resume(
        cls,
        manifest_path: str = DEFAULT_MANIFEST_PATH,
        state_path: str = DEFAULT_STATE_PATH,
    ) -> RuntimeInstance | None:
        """Restore a RuntimeInstance from persisted manifest and state.

        Process:
            1. Load RuntimeManifest — returns None if no previous runtime
            2. Resolve graph from manifest.graph_path
            3. Load UserState
            4. Reconstruct RuntimeInstance with preserved identity

        Returns:
            RuntimeInstance on success, None when no manifest exists.

        Raises:
            RecoveryError: Graph package moved/deleted or state corrupted.
        """
        raw = _storage_load_manifest(manifest_path)
        if raw is None:
            return None  # No previous runtime session

        manifest = RuntimeManifest.from_dict(raw)
        if not manifest.graph_path:
            return None  # Incomplete manifest

        try:
            graph = cls._load_graph(manifest.graph_path)
        except LOSError:
            raise RecoveryError(
                f"Graph package not found: {manifest.graph_path}"
            )

        # Use per-graph state path derived from manifest's graph_id,
        # falling back to the caller-provided state_path for backward compat.
        resolved_state_path = state_path_for_graph(manifest.graph_id or "")
        if resolved_state_path == DEFAULT_STATE_PATH:
            resolved_state_path = state_path
        state = _storage_load(resolved_state_path)

        runtime = cls(graph=graph, state=state)
        runtime._runtime_id = manifest.runtime_id  # Preserve identity
        runtime._manifest = manifest
        runtime._transition(RuntimeStatus.ACTIVE)

        return runtime

    # ── internal helpers (Constraint 2 — separate methods) ──────────

    @staticmethod
    def _load_graph(package_path: str) -> LoadedGraph:
        """Load and validate a Graph Package from disk.

        Raises:
            LOSError, yaml.YAMLError: Graph loading or validation failure.
        """
        return load_graph_package(package_path)

    @staticmethod
    def _initialize_state(
        graph: LoadedGraph, package_path: str
    ) -> StateAccess:
        """Load or create UserState and sync with graph nodes.

        Uses per-graph state isolation: state is stored at
        data/user-state-{graph_id}.json so each graph has independent progress.

        Returns a StateAccess-compatible handle (UserState at runtime).
        Sets backward-compat graph metadata (graph_id, graph_version).
        """
        state_path = state_path_for_graph(graph.package_id)
        us = _storage_load(state_path)
        node_ids = [n.id for n in graph.get_all_nodes()]
        sync_node_states(us, node_ids)
        us.graph_id = graph.package_id
        us.graph_version = graph.package_version
        return us  # UserState structurally satisfies StateAccess

    # ── public queries ──────────────────────────────────────────────

    def get_available_nodes(self) -> list[str]:
        """Return IDs of all AVAILABLE nodes in insertion order.

        Delegates to Resolver.
        """
        return get_available_nodes(self)

    def get_node_detail(self, node_id: str) -> dict | None:
        """Return detailed information about *node_id*, or None if unknown.

        Aggregates Graph metadata + derived availability (Resolver)
        + stored score/evidence/custom_dims (State contract methods).
        """
        node = self._graph.get_node(node_id)
        if node is None:
            return None

        derived = compute_availability(self).get(node_id, "UNKNOWN")
        evidence = self._state.get_evidence(node_id)
        evidence_str = ", ".join(evidence) if evidence else "(none)"
        resources = [
            {"type": r.type, "uri": r.uri, "label": r.label or ""}
            for r in getattr(node, "resources", [])
        ]

        ns = self._state.get_node_state(node_id)
        custom_dims = dict(ns.custom_dims) if ns and hasattr(ns, "custom_dims") else {}
        score_val = self._state.get_score(node_id)
        proficiency = _get_proficiency(score_val)

        return {
            "id": node.id,
            "title": node.title,
            "description": node.description,
            "type": node.type or "(none)",
            "difficulty": node.difficulty or "(none)",
            "status": derived,
            "score": score_val,
            "proficiency": proficiency,
            "evidence": evidence_str,
            "resources": resources,
            "custom_dims": custom_dims,
        }

    def get_progress(self) -> dict:
        """Return progress summary + availability counts.

        Returns a dict for CLI compatibility.
        Phase 3 debt: should return ProgressSnapshot per StateReader contract.
        """
        progress = _state_get_progress(self._state)  # {total, completed, mastered, percentage}
        statuses = compute_availability(self)
        available = sum(1 for v in statuses.values() if v == "AVAILABLE")
        locked = sum(1 for v in statuses.values() if v == "LOCKED")
        return {
            **progress,
            "available": available,
            "locked": locked,
        }

    def get_progress_snapshot(self) -> ProgressSnapshot:
        """Return a typed progress snapshot (StateReader contract).

        Does NOT include available/locked counts — those are
        Runtime-specific and belong to get_progress().
        """
        progress = _state_get_progress(self._state)
        return ProgressSnapshot(
            total=progress["total"],
            completed=progress["completed"],
            mastered=progress["mastered"],
            percentage=progress["percentage"],
        )

    def get_graph_info(self) -> dict:
        """Return current Graph Package metadata summary."""
        return {
            "package_id": self._graph.package_id,
            "package_name": self._graph.package_name,
            "package_version": self._graph.package_version,
            "author": self._graph.author or "(none)",
            "node_count": self._graph.node_count,
            "edge_count": self._graph.edge_count,
        }

    # ── mutation ────────────────────────────────────────────────────

    def complete_node(
        self,
        node_id: str,
        score: int = 10,
        evidence: list[str] | None = None,
    ) -> str:
        """Validate eligibility and complete a node.

        Delegates:
          1. can_complete_node (Resolver) — eligibility check
          2. self._mutator.complete_node (StateMutator) — state mutation
          3. save (Storage) — persistence

        Returns a completion message string.

        Raises:
            ValueError: If the node cannot be completed (unknown, already
                        completed, or prerequisites not met).
        """
        ok, reason = can_complete_node(self, node_id)
        if not ok:
            raise ValueError(f"Cannot complete '{node_id}': {reason}")

        node = self._graph.get_node(node_id)
        # node is guaranteed non-None by can_complete_node validation

        result = self._mutator.complete_node(
            node_id, score=score, evidence=evidence
        )

        if not result.success:
            raise ValueError(
                f"Cannot complete '{node_id}': {result.message}"
            )

        # ── XP integration (Phase 7) ──
        base_xp, boss_bonus = _earn_xp(node, score, self._state)
        xp_earned = base_xp + boss_bonus
        self._global_state.add_xp(xp_earned)

        # ── Add to global learning history ──
        from los.state.models import HistoryEntry
        self._global_state.add_history(HistoryEntry(
            node_id=node_id,
            field="complete",
            old_value="NOT_STARTED",
            new_value="COMPLETED",
            timestamp=_utc_now_iso(),
            description=f"Completed with score {score}",
        ))

        # ── Back-patch XP into the undo entry (frozen dataclass → replace) ──
        if self._state.undo_stack:
            last_ue = self._state.undo_stack[-1]
            if last_ue.node_id == node_id:
                self._state.undo_stack[-1] = UndoEntry(
                    node_id=last_ue.node_id,
                    action=last_ue.action,
                    previous_status=last_ue.previous_status,
                    previous_score=last_ue.previous_score,
                    previous_evidence=last_ue.previous_evidence,
                    previous_custom_dims=dict(last_ue.previous_custom_dims),
                    xp_earned=xp_earned,
                    timestamp=last_ue.timestamp,
                )

        self.save()

        # ── Build completion message ──
        msg = (
            f"Completed: {node.title} "
            f"(score: {self._state.get_score(node_id)}, +{base_xp} XP"
        )
        if boss_bonus > 0:
            msg += f", +{boss_bonus} Boss 奖励"
        msg += ")"
        return msg

    def reset_node(self, node_id: str) -> str:
        """Reset a node back to NOT_STARTED.

        Delegates:
          1. self._mutator.reset_node (StateMutator) — state mutation
          2. save (Storage) — persistence

        Returns a reset message string.

        Raises:
            ValueError: If the node is unknown.
        """
        node = self._graph.get_node(node_id)
        if node is None:
            raise ValueError(f"Cannot reset: unknown node '{node_id}'")

        result = self._mutator.reset_node(node_id)

        if not result.success:
            raise ValueError(
                f"Cannot reset '{node_id}': {result.message}"
            )

        self.save()

        return f"Reset: {node.title} → NOT_STARTED"

    def add_score_event(
        self,
        node_id: str,
        score_delta: int,
        description: str = "",
    ) -> str:
        """Add a self-assessment score event to a node.

        This is the self-assessment mechanism:
          - User describes what they did (e.g., "学习架构")
          - System adds score_delta to accumulated score
          - If accumulated score >= MASTERED_THRESHOLD (80) AND the node
            is COMPLETED, auto-promote to MASTERED.
          - XP is earned based on score_delta and node difficulty.

        Delegates:
          1. self._mutator.add_score_event (StateMutator)
          2. XP calculation and accrual
          3. save (Storage)

        Returns a descriptive message with new total score.

        Raises:
            ValueError: If the node is unknown or score_delta <= 0.
        """
        node = self._graph.get_node(node_id)
        if node is None:
            raise ValueError(f"Cannot score: unknown node '{node_id}'")

        previous_score = self._state.get_score(node_id)
        result = self._mutator.add_score_event(node_id, score_delta, description)

        if not result.success:
            raise ValueError(
                f"Cannot score '{node_id}': {result.message}"
            )

        # ── XP integration: earn XP for every score event ──
        xp_earned = _calculate_xp(
            getattr(node, "difficulty", None),
            score_delta,
            previous_score,
        )
        self._state.add_xp(xp_earned)
        self._global_state.add_xp(xp_earned)

        # ── Add to global learning history ──
        from los.state.models import HistoryEntry
        self._global_state.add_history(HistoryEntry(
            node_id=node_id,
            field="score",
            old_value=str(previous_score),
            new_value=str(previous_score + score_delta),
            timestamp=_utc_now_iso(),
            description=description,
        ))

        # ── Back-patch XP into the undo entry so undo can deduct it ──
        if self._state.undo_stack:
            last_ue = self._state.undo_stack[-1]
            if last_ue.node_id == node_id:
                self._state.undo_stack[-1] = UndoEntry(
                    node_id=last_ue.node_id,
                    action=last_ue.action,
                    previous_status=last_ue.previous_status,
                    previous_score=last_ue.previous_score,
                    previous_evidence=last_ue.previous_evidence,
                    previous_custom_dims=dict(last_ue.previous_custom_dims),
                    xp_earned=last_ue.xp_earned + xp_earned,
                    timestamp=last_ue.timestamp,
                )

        self.save()

        new_total = self._state.get_score(node_id)
        return f"Score: +{score_delta} → {new_total} total (+{xp_earned} XP)"

    def add_custom_dim_score(
        self,
        node_id: str,
        dim_name: str,
        score: int,
    ) -> str:
        """Set or update a custom scoring dimension for a node.

        Delegates:
          1. self._mutator.add_custom_dim_score (StateMutator)
          2. save (Storage)

        Returns a descriptive message.

        Raises:
            ValueError: If the node is unknown or validation fails.
        """
        node = self._graph.get_node(node_id)
        if node is None:
            raise ValueError(f"Unknown node '{node_id}'")

        result = self._mutator.add_custom_dim_score(node_id, dim_name, score)

        if not result.success:
            raise ValueError(
                f"Cannot set custom dim for '{node_id}': {result.message}"
            )

        self.save()

        return result.message

    def remove_custom_dim(
        self,
        node_id: str,
        dim_name: str,
    ) -> str:
        """Remove a custom scoring dimension from a node.

        Delegates:
          1. self._mutator.remove_custom_dim (StateMutator)
          2. save (Storage)

        Returns a descriptive message.

        Raises:
            ValueError: If the node is unknown or dim not found.
        """
        node = self._graph.get_node(node_id)
        if node is None:
            raise ValueError(f"Unknown node '{node_id}'")

        result = self._mutator.remove_custom_dim(node_id, dim_name)

        if not result.success:
            raise ValueError(
                f"Cannot remove custom dim for '{node_id}': {result.message}"
            )

        self.save()

        return result.message

    def undo_last_action(self) -> str:
        """Step-based undo: reverse the most recent node mutation.

        Pops the last UndoEntry from the stack, restores the node's
        pre-mutation state (status, score, evidence), and deducts XP
        from both the graph-level UserState and the global GlobalUserState.

        Delegates:
          1. self._mutator.undo_last (StateMutator)
          2. save (Storage)

        Returns an undo message string.

        Raises:
            ValueError: If the undo stack is empty.
        """
        if not self._state.undo_stack:
            raise ValueError("Undo stack is empty — nothing to undo")

        entry = self._state.undo_stack[-1]
        xp_to_deduct = entry.xp_earned

        result = self._mutator.undo_last()

        if not result.success:
            raise ValueError(
                f"Cannot undo: {result.message}"
            )

        if xp_to_deduct > 0:
            self._global_state.total_xp = max(0, self._global_state.total_xp - xp_to_deduct)

        node = self._graph.get_node(result.node_id)
        title = node.title if node else result.node_id

        self.save()

        return (
            f"Undone: {title} "
            f"(restored to {self._state.get_status(result.node_id)})"
        )

    def undo_multiple(self, count: int) -> list[UndoEntry]:
        """Undo multiple steps at once (infinite undo support).

        Undoes up to *count* steps from the undo stack.
        Returns the list of consumed UndoEntry objects.
        """
        from los.state.engine import undo_multiple

        if count < 1:
            raise ValueError("count must be >= 1")

        results = undo_multiple(self._state, count)
        self.save()
        return results

    def preview_undo_impact(self) -> dict:
        """Preview the impact of the next undo operation.

        Checks the node at the top of the undo stack and finds all nodes
        in the graph that depend on it via blocking edges.  Returns a
        summary including:

        * ``node_id``: the node that would be undone
        * ``node_title``: human-readable title
        * ``has_impact``: whether any dependent nodes would be affected
        * ``affected``: list of affected dependent nodes with their status
        * ``blocked_count``: number of NOT_STARTED nodes that would become LOCKED
        * ``orphaned_count``: number of COMPLETED/MASTERED nodes that would
          lose their prerequisite (data integrity concern)

        Returns an empty dict with ``has_impact=False`` if the undo stack
        is empty or the undone node is not a blocking prerequisite for
        anything.
        """
        if not self._state.undo_stack:
            return {"has_impact": False, "reason": "Undo stack is empty"}

        top_entry = self._state.undo_stack[-1]
        undone_node_id = top_entry.node_id

        node = self._graph.get_node(undone_node_id)
        node_title = node.title if node else undone_node_id

        # Collect all dependent nodes via blocking edges
        affected = []
        blocked_count = 0
        orphaned_count = 0

        for edge in self._graph.get_all_edges():
            # Find edges where the undone node is the source of a blocking edge
            if edge.source != undone_node_id:
                continue
            if edge.relation not in ("prerequisite", "dependency", "progression"):
                continue

            target_id = edge.target
            if not self._state.is_tracked(target_id):
                continue

            target_status = self._state.get_status(target_id)

            if target_status in ("COMPLETED", "MASTERED"):
                orphaned_count += 1
                affected.append({
                    "node_id": target_id,
                    "title": (self._graph.get_node(target_id) or target_id).title if self._graph.get_node(target_id) else target_id,
                    "status": target_status,
                    "impact": "orphaned",
                    "description": f"节点 '{target_id}' 已完成但将失去前置条件",
                })
            elif target_status == "NOT_STARTED":
                blocked_count += 1
                affected.append({
                    "node_id": target_id,
                    "title": (self._graph.get_node(target_id) or target_id).title if self._graph.get_node(target_id) else target_id,
                    "status": target_status,
                    "impact": "blocked",
                    "description": f"节点 '{target_id}' 将变为锁定状态",
                })

        has_impact = len(affected) > 0

        return {
            "has_impact": has_impact,
            "node_id": undone_node_id,
            "node_title": node_title,
            "previous_status": top_entry.previous_status,
            "affected": affected,
            "blocked_count": blocked_count,
            "orphaned_count": orphaned_count,
        }

    def undo_with_cascade(self, cascade: bool = False) -> dict:
        """Undo the last action, optionally cascading to affected dependent nodes.

        If *cascade* is True, also resets any COMPLETED/MASTERED dependent
        nodes that would lose their prerequisite, preventing orphaned state.

        Returns a summary dict with details of all undone/cascaded actions.
        """
        # 1. Preview impact first
        impact = self.preview_undo_impact()

        # 2. Perform the primary undo
        result = self._mutator.undo_last()
        if not result.success:
            raise ValueError(f"Cannot undo: {result.message}")

        node = self._graph.get_node(result.node_id)
        primary_title = node.title if node else result.node_id
        summary = {
            "primary": {
                "node_id": result.node_id,
                "title": primary_title,
                "restored_to": self._state.get_status(result.node_id),
            },
            "cascaded": [],
        }

        # 3. Cascade: reset orphaned dependent nodes
        if cascade and impact.get("orphaned_count", 0) > 0:
            for item in impact.get("affected", []):
                if item.get("impact") == "orphaned":
                    nid = item["node_id"]
                    self._mutator.reset_node(nid)
                    target_node = self._graph.get_node(nid)
                    summary["cascaded"].append({
                        "node_id": nid,
                        "title": target_node.title if target_node else nid,
                        "action": "reset",
                    })

        self.save()
        return summary

    def export_progress(self) -> dict:
        """Export current UserState as a serializable dict."""
        from los.storage.adapter import serialize

        return {
            "export_type": "user_progress",
            "schema_version": self._state.schema_version,
            "graph_id": self._state.graph_id,
            "graph_version": self._state.graph_version,
            "user_id": self._state.user_id,
            "created_at": self._state.created_at,
            "exported_at": self._state.updated_at,
            "data": serialize(self._state),
        }

    def import_progress(self, data: dict) -> str:
        """Import a previously exported UserState.

        Validates graph compatibility, replaces state, syncs nodes, and saves.
        Returns a status message string.
        """
        from los.storage.adapter import deserialize as _deserialize
        from los.state.engine import sync_node_states as _sync

        if data.get("export_type") != "user_progress":
            raise ValueError("Invalid export format: missing export_type")

        raw = data.get("data")
        if not raw:
            raise ValueError("Missing 'data' field in import payload")

        imported_state = _deserialize(raw)

        if imported_state.graph_id and imported_state.graph_id != self._graph.package_id:
            raise ValueError(
                f"Graph mismatch: import is '{imported_state.graph_id}', "
                f"current is '{self._graph.package_id}'"
            )

        self._state = imported_state
        node_ids = [n.id for n in self._graph.get_all_nodes()]
        _sync(self._state, node_ids)
        self._mutator = StateHandle(self._state)
        self.save()

        progress = self.get_progress()
        return (
            f"Progress imported: {progress['completed']}/{progress['total']} nodes completed"
        )

    # ── persistence ─────────────────────────────────────────────────

    def save(self) -> None:
        """Persist UserState and RuntimeManifest.

        Uses per-graph state isolation via state_path_for_graph.
        Saves both artifacts:
          - UserState → data/user-state-{graph_id}.json
          - RuntimeManifest → data/runtime-manifest.json
          - GlobalUserState → data/user-global-state.json (cross-graph persistence)
        """
        state_path = state_path_for_graph(self._graph.package_id)
        _storage_save(self._state, state_path)
        _storage_save_global(self._global_state)
        if self._manifest is not None:
            self._manifest.last_active = _utc_now_iso()
            _storage_save_manifest(self._manifest.to_dict())

    # ── ResolutionInput delegation (Constraint 1 — one-liners) ──────

    # GraphReader methods
    def get_node_ids(self) -> list[str]:
        return self._graph.get_node_ids()

    def node_exists(self, node_id: str) -> bool:
        return self._graph.node_exists(node_id)

    def get_blocking_source_ids(self, node_id: str) -> list[str]:
        return self._graph.get_blocking_source_ids(node_id)

    # StateReader methods
    def is_tracked(self, node_id: str) -> bool:
        return self._state.is_tracked(node_id)

    def is_completed(self, node_id: str) -> bool:
        return self._state.is_completed(node_id)

    def get_status(self, node_id: str) -> str:
        return self._state.get_status(node_id)

    def get_score(self, node_id: str) -> int:
        return self._state.get_score(node_id)

    def get_evidence(self, node_id: str) -> list[str]:
        return self._state.get_evidence(node_id)
