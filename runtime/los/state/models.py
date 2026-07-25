"""State data models — UserState and NodeState dataclasses.

Defined by:
  - LOS-0201 State Model
  - LOS-0404 State Engine
  - LOS-0405 Storage Adapter

The State layer is independent from Graph definitions.  A Graph describes
*what can be learned*; a UserState records *what a specific user has done*.
This separation is the fundamental architectural principle of Learning OS.

No graph, engine, or cli imports — pure data models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


# ── Schema version (LOS-0405) ──────────────────────────────────────────

CURRENT_SCHEMA_VERSION = "1.0.0"


# ── Node Status Enum (LOS-0404) ────────────────────────────────────────


class NodeStatus(str, Enum):
    """The four stored learning statuses (LOS-0404).

    ``Locked`` and ``Available`` from LOS-0201 are *derived* states
    calculated at runtime from Graph + State — they are never persisted.
    """

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    MASTERED = "MASTERED"


# ── Undo Stack (Step-based undo system) ────────────────────────────────

MAX_UNDO_STEPS = 0  # 0 = unlimited (infinite undo)
COMPLETED_THRESHOLD = 5  # score >= this → auto-promote to COMPLETED (unlocks downstream)
MASTERED_THRESHOLD = 80  # score >= this → auto-promote to MASTERED

# ── Default recommended score presets (used when graph doesn't specify) ──

DEFAULT_SCORE_PRESETS = [
    {"label": "了解一下", "score": 1},
    {"label": "认真学了", "score": 5},
    {"label": "动手实践", "score": 10},
    {"label": "举一反三", "score": 20},
    {"label": "项目实战", "score": 50},
    {"label": "传授他人", "score": 80},
]


@dataclass(frozen=True)
class UndoEntry:
    """Captures a node's pre-mutation state for step-based undo.

    Stored before each complete_node / start_node call.
    On undo, the entire entry is consumed — restoring status, score, evidence,
    custom_dims, and rolling back XP.
    """

    node_id: str
    action: str  # "complete" | "start"
    previous_status: str  # NodeStatus value before mutation
    previous_score: int
    previous_evidence: list[str]
    previous_custom_dims: dict[str, int] = field(default_factory=dict)
    xp_earned: int = 0  # XP gained by this action (deducted on undo)
    timestamp: str = ""


# ── History Entry (LOS-0404) ───────────────────────────────────────────


@dataclass(frozen=True)
class HistoryEntry:
    """An immutable record of a single state change.

    LOS-0404: "The State Engine SHOULD record important changes."
    """

    node_id: str
    field: str
    old_value: str
    new_value: str
    timestamp: str
    description: str = ""  # optional human-readable description (e.g. score event text)

    def __post_init__(self) -> None:
        for name in ("node_id", "field", "timestamp"):
            if not getattr(self, name):
                raise ValueError(f"HistoryEntry.{name} must not be empty")


# ── Node State (LOS-0201, LOS-0404) ────────────────────────────────────


@dataclass
class NodeState:
    """The user's relationship with a single learning Node.

    LOS-0201: Node States are stored separately from Graph definitions.
    LOS-0405: Storage references Node by ``node_id``, never by title.

    Fields:
        node_id     — reference to a Graph Node (primary key)
        status      — current learning status (NOT_STARTED by default)
        score       — user-defined progress value (0–100 range recommended)
        evidence    — optional text references to learning artifacts
        custom_dims — custom scoring dimensions (dim_name -> 0-100 int score)
        updated_at  — ISO-8601 timestamp of last modification
    """

    node_id: str
    status: NodeStatus = NodeStatus.NOT_STARTED
    score: int = 0
    evidence: list[str] = field(default_factory=list)
    custom_dims: dict[str, int] = field(default_factory=dict)
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.node_id.strip():
            raise ValueError("NodeState.node_id must not be empty")
        if self.score < 0:
            raise ValueError(f"NodeState.score must be >= 0, got {self.score}")
        # Validate custom_dims constraints
        for dim_name, dim_score in self.custom_dims.items():
            if not dim_name or not dim_name.strip():
                raise ValueError("custom_dims key must not be empty")
            if len(dim_name) > 32:
                raise ValueError(f"custom_dims key '{dim_name}' exceeds 32 chars")
            if not isinstance(dim_score, int):
                raise ValueError(f"custom_dims['{dim_name}'] must be int")
            if dim_score < 0 or dim_score > 100:
                raise ValueError(f"custom_dims['{dim_name}'] must be 0-100, got {dim_score}")
        if not self.updated_at:
            self.updated_at = _utc_now_iso()

    @property
    def is_completed(self) -> bool:
        """True when the user considers the Node substantially done."""
        return self.status in (NodeStatus.COMPLETED, NodeStatus.MASTERED)


# ── Progress Snapshot (CT-002) ─────────────────────────────────────────


@dataclass(frozen=True)
class _Progress:
    """Internal progress summary — structurally compatible with
    ``los.runtime.contracts.state_access.ProgressSnapshot``.

    Defined here (not imported from the contract) to avoid a reverse
    dependency: state → runtime.
    """

    total: int
    completed: int
    mastered: int
    percentage: float


# ── User State (LOS-0201, LOS-0404, LOS-0405) ──────────────────────────


@dataclass
class UserState:
    """The complete representation of one user's interaction with one Graph.

    LOS-0405 structure:
        user_id        — identity
        graph_id       — reference to the loaded Graph Package (soft-deprecated — RuntimeManifest is authoritative)
        graph_version  — version of the loaded Graph Package (soft-deprecated — RuntimeManifest is authoritative)
        node_states    — dict of node_id → NodeState
        history        — ordered log of state changes
        schema_version — stored data format version
        created_at     — when this UserState was first created
        updated_at     — when this UserState was last modified
    """

    user_id: str = "default"
    graph_id: str = ""
    graph_version: str = ""
    node_states: dict[str, NodeState] = field(default_factory=dict)
    history: list[HistoryEntry] = field(default_factory=list)
    undo_stack: list[UndoEntry] = field(default_factory=list)
    schema_version: str = CURRENT_SCHEMA_VERSION
    created_at: str = ""
    updated_at: str = ""
    total_xp: int = 0

    def __post_init__(self) -> None:
        now = _utc_now_iso()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    # ── XP (Phase 7) ─────────────────────────────────────────────────

    def add_xp(self, amount: int) -> None:
        """Add *amount* to total_xp and update timestamp."""
        self.total_xp += amount
        self.updated_at = _utc_now_iso()

    # ── helpers ────────────────────────────────────────────────────────

    def get_node_state(self, node_id: str) -> NodeState | None:
        """Return the NodeState for *node_id*, or None if not present."""
        return self.node_states.get(node_id)

    def ensure_node_state(self, node_id: str) -> NodeState:
        """Return the NodeState for *node_id*, creating one if absent."""
        ns = self.node_states.get(node_id)
        if ns is None:
            ns = NodeState(node_id=node_id)
            self.node_states[node_id] = ns
        return ns

    @property
    def completed_count(self) -> int:
        """Number of Nodes with status COMPLETED or MASTERED."""
        return sum(1 for ns in self.node_states.values() if ns.is_completed)

    @property
    def total_count(self) -> int:
        """Total number of tracked Nodes."""
        return len(self.node_states)

    # ── semantic queries (CT-002 StateReader contract) ──────────────

    def is_tracked(self, node_id: str) -> bool:
        """Return True if *node_id* has a state entry."""
        return node_id in self.node_states

    def is_completed(self, node_id: str) -> bool:
        """Return True if *node_id* is COMPLETED or MASTERED."""
        ns = self.node_states.get(node_id)
        return ns.is_completed if ns else False

    def get_status(self, node_id: str) -> str:
        """Return the status string for *node_id*.

        Returns 'NOT_STARTED' if the node is not tracked.
        """
        ns = self.node_states.get(node_id)
        return ns.status.value if ns else NodeStatus.NOT_STARTED.value

    def get_score(self, node_id: str) -> int:
        """Return the score for *node_id*, or 0 if not tracked."""
        ns = self.node_states.get(node_id)
        return ns.score if ns else 0

    def get_evidence(self, node_id: str) -> list[str]:
        """Return evidence references for *node_id*.

        Returns an empty list if the node is not tracked.
        """
        ns = self.node_states.get(node_id)
        return list(ns.evidence) if ns else []

    def get_progress(self):
        """Return an immutable progress summary."""
        total = len(self.node_states)
        completed = 0
        mastered = 0
        for ns in self.node_states.values():
            if ns.status == NodeStatus.MASTERED:
                mastered += 1
                completed += 1
            elif ns.status == NodeStatus.COMPLETED:
                completed += 1
        pct = (completed / total * 100.0) if total > 0 else 0.0
        return _Progress(
            total=total,
            completed=completed,
            mastered=mastered,
            percentage=round(pct, 1),
        )


# ── Global User State (user-level, cross-graph persistence) ──────────────


@dataclass
class GlobalUserState:
    """The user-level state that persists across graphs.

    This stores XP, achievements, and learning history that should NOT
    be reset when a single graph's progress is cleared.

    Fields:
        user_id              — identity (always "default" for now)
        total_xp             — accumulated XP across all graphs
        unlocked_achievements — list of achievement IDs that are unlocked
        learning_history     — all score and completion events across graphs
        created_at           — when this GlobalUserState was first created
        updated_at           — when this GlobalUserState was last modified
        schema_version       — stored data format version
    """

    user_id: str = "default"
    total_xp: int = 0
    unlocked_achievements: list[str] = field(default_factory=list)
    learning_history: list[HistoryEntry] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    schema_version: str = CURRENT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        now = _utc_now_iso()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def add_xp(self, amount: int) -> None:
        """Add *amount* to total_xp and update timestamp."""
        self.total_xp += amount
        self.updated_at = _utc_now_iso()

    def add_history(self, entry: HistoryEntry) -> None:
        """Add a history entry to the global learning history."""
        self.learning_history.append(entry)
        self.updated_at = _utc_now_iso()

    def unlock_achievement(self, achievement_id: str) -> bool:
        """Unlock an achievement by ID. Returns True if newly unlocked."""
        if achievement_id not in self.unlocked_achievements:
            self.unlocked_achievements.append(achievement_id)
            self.updated_at = _utc_now_iso()
            return True
        return False

    def is_achievement_unlocked(self, achievement_id: str) -> bool:
        """Return True if the achievement is already unlocked."""
        return achievement_id in self.unlocked_achievements


# ── internal helpers ───────────────────────────────────────────────────


from los.common import utc_now_iso as _utc_now_iso
