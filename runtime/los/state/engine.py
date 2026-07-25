"""State Engine — manage UserState Node progress.

Defined by:
  - LOS-0201 State Model
  - LOS-0200 Runtime Overview
  - LOS-0404 State Engine
  - Phase 6 Design Review

Pure state operations layer.  The State Engine knows nothing about Graph
structure and does not compute availability — those responsibilities
belong to the Runtime Engine (Phase 7).

Allowed imports:
  - los.state.models  (NodeState, UserState, NodeStatus, HistoryEntry)
"""

from __future__ import annotations

from los.common import utc_now_iso as _utc_now_iso
from los.exceptions import (
    InvalidStateTransitionError,
    NodeAlreadyCompletedError,
    NodeNotFoundError,
)
from los.runtime.contracts.state_access import MutationResult
from los.state.models import (
    COMPLETED_THRESHOLD,
    HistoryEntry,
    MASTERED_THRESHOLD,
    MAX_UNDO_STEPS,
    NodeState,
    NodeStatus,
    UndoEntry,
    UserState,
)


# ── Public API ─────────────────────────────────────────────────────────


def sync_node_states(us: UserState, node_ids: list[str]) -> UserState:
    """Ensure every *node_id* has a corresponding NodeState entry.

    Missing entries are created with ``NOT_STARTED`` / score 0.
    Existing entries are **never** overwritten.

    Idempotent — safe to call multiple times with the same graph.
    Mutates *us* in place.  Returns *us* for chaining convenience.
    """
    for nid in node_ids:
        if nid not in us.node_states:
            us.node_states[nid] = NodeState(node_id=nid)
    return us


def complete_node(
    us: UserState,
    node_id: str,
    score: int = 10,
    evidence: list[str] | None = None,
) -> HistoryEntry:
    """Mark a Node as COMPLETED.

    1. Look up the NodeState → :class:`NodeNotFoundError` if not found.
    2. Validate current status → :class:`NodeAlreadyCompletedError` if already COMPLETED
       or MASTERED.
    3. **Capture pre-state** → push UndoEntry to undo_stack (max 10 steps).
    4. Advance status to COMPLETED.
    5. Set score to ``max(old_score, new_score)`` (non-decreasing).
    6. Append *evidence* entries if provided.
    7. Refresh ``updated_at`` on both the NodeState and UserState.
    8. Generate and append a :class:`HistoryEntry`.

    Returns the created :class:`HistoryEntry`.
    """
    ns = _require_node_state(us, node_id)

    if ns.is_completed:
        raise NodeAlreadyCompletedError(
            f"Node '{node_id}' is already {ns.status.value}; cannot re-complete"
        )

    # ── Step-based undo: capture pre-state before mutation ──
    _push_undo(us, node_id, "complete", ns)

    old_status = ns.status.value
    old_score = ns.score

    # Non-decreasing score
    ns.score = max(old_score, score)

    # ── Auto-MASTERED: score >= threshold → promote ──
    new_status = NodeStatus.COMPLETED
    if ns.score >= MASTERED_THRESHOLD:
        new_status = NodeStatus.MASTERED

    # Advance status (COMPLETED or MASTERED)
    ns.status = new_status

    # Append evidence
    if evidence:
        ns.evidence.extend(evidence)

    # Timestamps
    now = _utc_now_iso()
    ns.updated_at = now
    _bump_user_state(us, now)

    # History
    he = HistoryEntry(
        node_id=node_id,
        field="status",
        old_value=old_status,
        new_value=new_status.value,
        timestamp=now,
    )
    us.history.append(he)

    # If score changed, log that too
    if ns.score != old_score:
        he_score = HistoryEntry(
            node_id=node_id,
            field="score",
            old_value=str(old_score),
            new_value=str(ns.score),
            timestamp=now,
        )
        us.history.append(he_score)

    return he


def undo_last_action(us: UserState) -> UndoEntry:
    """Pop the last UndoEntry from the stack and restore the node's pre-mutation state.

    This is the step-based undo — only the most recent action is reversed.
    Restores status, score, evidence, custom_dims, and deducts any XP earned.

    Returns:
        The consumed UndoEntry.

    Raises:
        IndexError: If the undo stack is empty.
    """
    if not us.undo_stack:
        raise IndexError("Undo stack is empty — nothing to undo")

    entry = us.undo_stack.pop()

    # Restore node state
    ns = us.ensure_node_state(entry.node_id)
    ns.status = NodeStatus(entry.previous_status)
    ns.score = entry.previous_score
    ns.evidence = list(entry.previous_evidence)
    ns.custom_dims = dict(entry.previous_custom_dims)

    # Roll back XP
    if entry.xp_earned > 0:
        us.total_xp = max(0, us.total_xp - entry.xp_earned)

    now = _utc_now_iso()
    ns.updated_at = now
    _bump_user_state(us, now)

    # Record undo in history
    he = HistoryEntry(
        node_id=entry.node_id,
        field="undo",
        old_value=f"{entry.action}:{entry.previous_status}",
        new_value=f"RESTORED:{entry.previous_status}",
        timestamp=now,
    )
    us.history.append(he)

    return entry


def add_score_event(
    us: UserState,
    node_id: str,
    score_delta: int,
    description: str = "",
) -> HistoryEntry:
    """Add a score event to a node, auto-promoting status when thresholds reached.

    Proficiency-aligned auto-promotion:
      - score >= 5  AND not yet completed → COMPLETED  (unlocks downstream nodes)
      - score >= 80 AND already COMPLETED  → MASTERED  (Master level)

    Score is always non-decreasing.
    Evidence is appended with formatted event record.
    Undo entry is pushed BEFORE mutation for single-step score undo.

    Returns the created HistoryEntry.
    """
    ns = _require_node_state(us, node_id)
    if score_delta <= 0:
        raise ValueError(f"score_delta must be > 0, got {score_delta}")

    # ── Step-based undo: capture pre-state before score mutation ──
    _push_undo(us, node_id, "score", ns)

    old_status = ns.status
    old_score = ns.score
    ns.score = old_score + score_delta

    # Format event record
    desc_suffix = f": {description}" if description else ""
    event_record = f"[{_utc_now_iso()}] +{score_delta}pts{desc_suffix}"
    ns.evidence.append(event_record)

    now = _utc_now_iso()
    ns.updated_at = now
    _bump_user_state(us, now)

    # ── Proficiency-aligned auto-promotion ──
    new_status = ns.status
    status_changed = False

    if not ns.is_completed and ns.score >= COMPLETED_THRESHOLD:
        new_status = NodeStatus.COMPLETED
        ns.status = new_status
        status_changed = True
    elif ns.is_completed and ns.score >= MASTERED_THRESHOLD and ns.status != NodeStatus.MASTERED:
        new_status = NodeStatus.MASTERED
        ns.status = new_status
        status_changed = True

    # History — score change
    he = HistoryEntry(
        node_id=node_id,
        field="score",
        old_value=str(old_score),
        new_value=str(ns.score),
        timestamp=now,
        description=description,
    )
    us.history.append(he)

    # History — status change (if auto-promoted)
    if status_changed:
        he2 = HistoryEntry(
            node_id=node_id,
            field="status",
            old_value=old_status.value if old_status != NodeStatus.NOT_STARTED else "NOT_STARTED",
            new_value=new_status.value,
            timestamp=now,
            description=f"auto-promoted: score {ns.score} >= threshold",
        )
        us.history.append(he2)

    return he


def undo_multiple(us: UserState, count: int) -> list[UndoEntry]:
    """Undo multiple steps at once, returning all consumed entries.

    Entries are returned in the order they were undone (most recent first).
    If count > stack size, undoes everything and returns all entries.
    """
    if count < 1:
        raise ValueError(f"count must be >= 1, got {count}")
    results = []
    for _ in range(min(count, len(us.undo_stack))):
        results.append(undo_last_action(us))
    return results


def _push_undo(us: UserState, node_id: str, action: str, ns: NodeState) -> None:
    """Capture pre-mutation state and push to undo stack (max MAX_UNDO_STEPS)."""
    entry = UndoEntry(
        node_id=node_id,
        action=action,
        previous_status=ns.status.value,
        previous_score=ns.score,
        previous_evidence=list(ns.evidence),
        previous_custom_dims=dict(ns.custom_dims),
        xp_earned=0,  # filled by RuntimeInstance after XP calculation
        timestamp=_utc_now_iso(),
    )
    us.undo_stack.append(entry)
    # Trim to max steps (0 = unlimited)
    if MAX_UNDO_STEPS > 0 and len(us.undo_stack) > MAX_UNDO_STEPS:
        us.undo_stack = us.undo_stack[-MAX_UNDO_STEPS:]


def add_custom_dim_score(
    us: UserState,
    node_id: str,
    dim_name: str,
    score: int,
) -> tuple[int | None, str]:
    """Set or update a custom scoring dimension for a node.

    Args:
        us: UserState to mutate
        node_id: target node
        dim_name: dimension name (non-empty, <= 32 chars)
        score: int score between 0 and 100 inclusive

    Returns:
        (new_total_calc=None, message)
    """
    ns = _require_node_state(us, node_id)

    if dim_name is None:
        return None, "dim_name must not be None"
    if not isinstance(dim_name, str) or not dim_name.strip():
        return None, "dim_name must be a non-empty string"
    if len(dim_name) > 32:
        return None, f"dim_name exceeds 32 characters (got {len(dim_name)})"
    if not isinstance(score, int):
        return None, f"score must be int, got {type(score).__name__}"
    if score < 0 or score > 100:
        return None, f"score must be between 0 and 100, got {score}"

    old_value = ns.custom_dims.get(dim_name, 0)

    # Capture pre-state for undo
    _push_undo(us, node_id, "custom_dim", ns)

    # Apply mutation
    ns.custom_dims[dim_name] = score

    now = _utc_now_iso()
    ns.updated_at = now
    _bump_user_state(us, now)

    he = HistoryEntry(
        node_id=node_id,
        field=f"custom_dim:{dim_name}",
        old_value=str(old_value),
        new_value=str(score),
        timestamp=now,
    )
    us.history.append(he)

    return None, f"Set custom_dims['{dim_name}'] = {score}"


def start_node(us: UserState, node_id: str) -> HistoryEntry:
    """Mark a Node as IN_PROGRESS.

    Creates the NodeState entry if absent (from a pre-sync state).
    :class:`InvalidStateTransitionError` if the node is already IN_PROGRESS,
    COMPLETED, or MASTERED.
    """
    ns = us.node_states.get(node_id)
    if ns is None:
        ns = NodeState(node_id=node_id)
        us.node_states[node_id] = ns
        # No undo capture — this is a creation, not a mutation of existing state
    else:
        if ns.status != NodeStatus.NOT_STARTED:
            raise InvalidStateTransitionError(
                f"Node '{node_id}' is already {ns.status.value}; "
                f"cannot start (must be NOT_STARTED)"
            )
        # ── Step-based undo: capture pre-state ──
        _push_undo(us, node_id, "start", ns)

    old_status = ns.status.value
    now = _utc_now_iso()

    ns.status = NodeStatus.IN_PROGRESS
    ns.updated_at = now
    _bump_user_state(us, now)

    he = HistoryEntry(
        node_id=node_id,
        field="status",
        old_value=old_status,
        new_value=NodeStatus.IN_PROGRESS.value,
        timestamp=now,
    )
    us.history.append(he)
    return he


def reset_node(us: UserState, node_id: str) -> HistoryEntry:
    """Reset a Node back to NOT_STARTED.

    Works on any status (COMPLETED, MASTERED, IN_PROGRESS).
    1. Look up the NodeState → NodeNotFoundError if not found.
    2. Reset status to NOT_STARTED, score to 0, clear evidence.
    3. Refresh timestamps.
    4. Generate and append a HistoryEntry.

    Returns the created HistoryEntry.
    Ignores nodes already at NOT_STARTED (no-op with a log entry).
    """
    ns = _require_node_state(us, node_id)

    if ns.status == NodeStatus.NOT_STARTED:
        return HistoryEntry(
            node_id=node_id,
            field="status",
            old_value=NodeStatus.NOT_STARTED.value,
            new_value=NodeStatus.NOT_STARTED.value,
            timestamp=_utc_now_iso(),
        )

    old_status = ns.status.value
    old_score = ns.score

    ns.status = NodeStatus.NOT_STARTED
    ns.score = 0
    ns.evidence = []

    now = _utc_now_iso()
    ns.updated_at = now
    _bump_user_state(us, now)

    he = HistoryEntry(
        node_id=node_id,
        field="status",
        old_value=old_status,
        new_value=NodeStatus.NOT_STARTED.value,
        timestamp=now,
    )
    us.history.append(he)

    # Log score reset if there was a score
    if old_score > 0:
        he_score = HistoryEntry(
            node_id=node_id,
            field="score",
            old_value=str(old_score),
            new_value="0",
            timestamp=now,
        )
        us.history.append(he_score)

    return he


def get_progress(us: UserState) -> dict:
    """Return summary statistics.

    Keys: ``total``, ``completed``, ``mastered``, ``percentage``.
    ``percentage`` is ``completed / total * 100`` (0.0 when total is 0).
    """
    total = us.total_count
    completed = 0
    mastered = 0
    for ns in us.node_states.values():
        if ns.status == NodeStatus.MASTERED:
            mastered += 1
            completed += 1
        elif ns.status == NodeStatus.COMPLETED:
            completed += 1

    pct = (completed / total * 100.0) if total > 0 else 0.0
    return {
        "total": total,
        "completed": completed,
        "mastered": mastered,
        "percentage": round(pct, 1),
    }


def get_node_status(us: UserState, node_id: str) -> NodeStatus:
    """Return the stored status for *node_id*.

    :class:`NodeNotFoundError` if the node is not tracked.
    """
    ns = us.node_states.get(node_id)
    if ns is None:
        raise NodeNotFoundError(f"Node '{node_id}' is not tracked in UserState")
    return ns.status


# ── internal helpers ──────────────────────────────────────────────────


def _require_node_state(us: UserState, node_id: str) -> NodeState:
    ns = us.node_states.get(node_id)
    if ns is None:
        raise NodeNotFoundError(f"Node '{node_id}' is not tracked in UserState")
    return ns


def _bump_user_state(us: UserState, ts: str) -> None:
    us.updated_at = ts


# ── StateHandle — StateMutator adapter ─────────────────────────────────


class StateHandle:
    """Implement the StateMutator contract by wrapping a UserState.

    Consumer:
        RuntimeInstance (via StateMutator Protocol).

    Provider:
        State Authority.

    Responsibility:
        Adapt state engine mutation functions to the StateMutator
        contract boundary.  Delegates validation and commit to the
        existing State Engine — no redesign, no new logic.

    This is an adapter, NOT a new authority.
    """

    def __init__(self, us: UserState) -> None:
        self._us = us

    # ── StateMutator methods ──────────────────────────────────────

    def complete_node(
        self,
        node_id: str,
        score: int = 10,
        evidence: list[str] | None = None,
    ) -> MutationResult:
        """Mark *node_id* as COMPLETED.

        Returns:
            MutationResult(success=True, …) on success.
            MutationResult(success=False, …) with the engine error message
            on validation failure.
        """
        try:
            complete_node(self._us, node_id, score=score, evidence=evidence)
        except (NodeAlreadyCompletedError, NodeNotFoundError) as e:
            return MutationResult(success=False, node_id=node_id, message=str(e))
        return MutationResult(
            success=True, node_id=node_id, message=f"Node '{node_id}' completed"
        )

    def reset_node(self, node_id: str) -> MutationResult:
        """Reset *node_id* back to NOT_STARTED (hard reset).

        Returns:
            MutationResult(success=True, …) on success.
        """
        try:
            reset_node(self._us, node_id)
        except NodeNotFoundError as e:
            return MutationResult(success=False, node_id=node_id, message=str(e))
        return MutationResult(
            success=True, node_id=node_id, message=f"Node '{node_id}' reset"
        )

    def undo_last(self) -> MutationResult:
        """Undo the last action (step-based undo).

        Pops the most recent UndoEntry from the stack and restores
        the node's pre-mutation state.

        Returns:
            MutationResult(success=True, …) with the undone node_id on success.
        """
        try:
            entry = undo_last_action(self._us)
        except IndexError as e:
            return MutationResult(success=False, node_id="", message=str(e))
        return MutationResult(
            success=True,
            node_id=entry.node_id,
            message=f"Undone: {entry.node_id} → {entry.previous_status}",
        )

    def add_score_event(
        self, node_id: str, score_delta: int, description: str = ""
    ) -> MutationResult:
        """Add a score event (self-assessment) to *node_id*.

        Returns MutationResult with the new total score on success.
        """
        try:
            add_score_event(self._us, node_id, score_delta, description)
        except (NodeNotFoundError, ValueError) as e:
            return MutationResult(success=False, node_id=node_id, message=str(e))
        new_total = self._us.node_states[node_id].score
        return MutationResult(
            success=True,
            node_id=node_id,
            message=f"Score: +{score_delta} → {new_total} total",
        )

    def start_node(self, node_id: str) -> MutationResult:
        """Mark *node_id* as IN_PROGRESS.

        Returns:
            MutationResult(success=True, …) on success.
            MutationResult(success=False, …) with the engine error message
            on validation failure.
        """
        try:
            start_node(self._us, node_id)
        except InvalidStateTransitionError as e:
            return MutationResult(success=False, node_id=node_id, message=str(e))
        return MutationResult(
            success=True, node_id=node_id, message=f"Node '{node_id}' started"
        )

    def add_custom_dim_score(
        self, node_id: str, dim_name: str, score: int
    ) -> MutationResult:
        """Set or update a custom scoring dimension.

        Returns MutationResult with message on success.
        """
        try:
            _, msg = add_custom_dim_score(self._us, node_id, dim_name, score)
        except NodeNotFoundError as e:
            return MutationResult(success=False, node_id=node_id, message=str(e))
        return MutationResult(
            success=True,
            node_id=node_id,
            message=msg,
        )

    def remove_custom_dim(self, node_id: str, dim_name: str) -> MutationResult:
        """Remove a custom scoring dimension if it exists."""
        try:
            ns = _require_node_state(self._us, node_id)
        except NodeNotFoundError as e:
            return MutationResult(success=False, node_id=node_id, message=str(e))

        if dim_name not in ns.custom_dims:
            return MutationResult(
                success=False,
                node_id=node_id,
                message=f"Custom dim '{dim_name}' not found",
            )

        # Capture pre-state for undo
        _push_undo(self._us, node_id, "remove_custom_dim", ns)

        del ns.custom_dims[dim_name]

        now = _utc_now_iso()
        ns.updated_at = now
        _bump_user_state(self._us, now)

        return MutationResult(
            success=True,
            node_id=node_id,
            message=f"Removed custom_dims['{dim_name}']",
        )
