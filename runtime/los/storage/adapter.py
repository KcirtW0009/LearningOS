"""Storage Adapter — local JSON persistence for UserState and RuntimeManifest.

Defined by:
  - LOS-0203 Storage Model
  - LOS-0405 Storage Adapter
  - Phase 4 Persistence & Recovery (Approved)

Responsibilities:
  - save UserState to JSON
  - load UserState from JSON
  - save RuntimeManifest dict to JSON (dict-based — no Runtime import)
  - load RuntimeManifest dict from JSON (dict-based — no Runtime import)
  - preserve orphaned Node progress across Graph replacements
  - save/load GlobalUserState (user-level cross-graph state)

The Storage layer is the bottom dependency — it imports only los.exceptions
and los.state.models.  It never imports from los.runtime.
"""

from __future__ import annotations

import json
import os
from typing import Any

from los.exceptions import SchemaVersionError
from los.state.models import (
    CURRENT_SCHEMA_VERSION,
    GlobalUserState,
    HistoryEntry,
    NodeState,
    NodeStatus,
    UndoEntry,
    UserState,
)

# Default locations (relative to project root, overridable by env var)
_DATA_ROOT = os.environ.get("LEARNINGOS_DATA_DIR", "data")

DEFAULT_STATE_PATH = os.path.join(_DATA_ROOT, "user-state.json")
DEFAULT_MANIFEST_PATH = os.path.join(_DATA_ROOT, "runtime-manifest.json")
GLOBAL_STATE_PATH = os.path.join(_DATA_ROOT, "user-global-state.json")


def state_path_for_graph(graph_id: str) -> str:
    """Return the per-graph state file path.

    Uses data/user-state-{graph_id}.json for per-graph isolation.
    Falls back to data/user-state.json if graph_id is empty.
    """
    if not graph_id:
        return DEFAULT_STATE_PATH
    safe_id = graph_id.replace("/", "-").replace("\\", "-").replace(" ", "_")
    return os.path.join(_DATA_ROOT, f"user-state-{safe_id}.json")


# ── Public API ──────────────────────────────────────────────────────────


def ensure_data_dir() -> str:
    """Create ``data/`` directory if missing. Return its absolute path."""
    path = os.path.join(os.getcwd(), "data")
    os.makedirs(path, exist_ok=True)
    return path


def save(us: UserState, path: str = DEFAULT_STATE_PATH) -> None:
    """Persist *us* to *path* as JSON.

    Creates parent directories if they do not exist.
    """
    _bump_updated_at(us)
    _ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_user_state_to_dict(us), f, indent=2, ensure_ascii=False)


def load(path: str = DEFAULT_STATE_PATH) -> UserState:
    """Load and return the UserState stored at *path*.

    Returns a *new*, empty UserState if the file does not exist.
    Raises :class:`ValueError` if the file exists but contains invalid data.
    """
    if not os.path.isfile(path):
        return UserState()

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    _validate_schema_version(raw)
    return _dict_to_user_state(raw)


def exists(path: str = DEFAULT_STATE_PATH) -> bool:
    """Return ``True`` when a state file exists at *path*."""
    return os.path.isfile(path)


def serialize(us: UserState) -> dict[str, Any]:
    """Serialize a UserState to a plain dict (for export/API use)."""
    return _user_state_to_dict(us)


def deserialize(data: dict[str, Any]) -> UserState:
    """Deserialize a plain dict back into a UserState (for import/API use)."""
    return _dict_to_user_state(data)


# ── manifest persistence (dict-based — no Runtime imports) ────────────


def save_manifest(data: dict, path: str = DEFAULT_MANIFEST_PATH) -> None:
    """Persist a manifest dict as JSON.

    The caller (RuntimeInstance) converts RuntimeManifest → dict before
    calling.  This function knows nothing about Runtime types — it operates
    on plain ``dict`` objects only.
    """
    _ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_manifest(path: str = DEFAULT_MANIFEST_PATH) -> dict | None:
    """Load manifest data from JSON.

    Returns ``None`` if the file does not exist.  The caller is responsible
    for converting the returned dict into a RuntimeManifest.
    """
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def manifest_exists(path: str = DEFAULT_MANIFEST_PATH) -> bool:
    """Return ``True`` when a manifest file exists at *path*."""
    return os.path.isfile(path)


# ── serialization → dict ──────────────────────────────────────────────


def _user_state_to_dict(us: UserState) -> dict[str, Any]:
    node_states: dict[str, Any] = {}
    orphaned: dict[str, Any] = {}

    if us.graph_id:
        for nid, ns in us.node_states.items():
            node_states[nid] = _node_state_to_dict(ns)

    for nid, ns in us.node_states.items():
        # Nodes that pre-date the current graph are orphans
        pass  # handled during merge in engine — storage just serialises what it has

    return {
        "user_id": us.user_id,
        "graph_id": us.graph_id,
        "graph_version": us.graph_version,
        "schema_version": us.schema_version,
        "created_at": us.created_at,
        "updated_at": us.updated_at,
        "total_xp": us.total_xp,
        "node_states": node_states,
        "history": [_history_entry_to_dict(h) for h in us.history],
        "undo_stack": [_undo_entry_to_dict(u) for u in us.undo_stack],
    }


def _node_state_to_dict(ns: NodeState) -> dict[str, Any]:
    return {
        "node_id": ns.node_id,
        "status": ns.status.value,
        "score": ns.score,
        "evidence": ns.evidence,
        "custom_dims": ns.custom_dims,
        "updated_at": ns.updated_at,
    }


def _history_entry_to_dict(he: HistoryEntry) -> dict[str, Any]:
    d = {
        "node_id": he.node_id,
        "field": he.field,
        "old_value": he.old_value,
        "new_value": he.new_value,
        "timestamp": he.timestamp,
    }
    if he.description:
        d["description"] = he.description
    return d


def _undo_entry_to_dict(ue: UndoEntry) -> dict[str, Any]:
    return {
        "node_id": ue.node_id,
        "action": ue.action,
        "previous_status": ue.previous_status,
        "previous_score": ue.previous_score,
        "previous_evidence": ue.previous_evidence,
        "previous_custom_dims": ue.previous_custom_dims,
        "xp_earned": ue.xp_earned,
        "timestamp": ue.timestamp,
    }


# ── deserialization ← dict ────────────────────────────────────────────


def _validate_schema_version(raw: dict[str, Any]) -> None:
    stored = raw.get("schema_version", "")
    if not stored:
        raise SchemaVersionError("Missing schema_version in stored data")
    # v0.5.0 is lenient — future versions may enforce compatibility


def _dict_to_user_state(d: dict[str, Any]) -> UserState:
    us = UserState(
        user_id=d.get("user_id", "default"),
        graph_id=d.get("graph_id", ""),
        graph_version=d.get("graph_version", ""),
        schema_version=d.get("schema_version", CURRENT_SCHEMA_VERSION),
        created_at=d.get("created_at", ""),
        updated_at=d.get("updated_at", ""),
    )

    us.total_xp = int(d.get("total_xp", 0))

    raw_states: dict[str, Any] = d.get("node_states", {})
    for nid, raw_ns in raw_states.items():
        us.node_states[nid] = _dict_to_node_state(raw_ns)

    raw_hist: list[dict[str, Any]] = d.get("history", [])
    for h in raw_hist:
        us.history.append(_dict_to_history_entry(h))

    raw_undo: list[dict[str, Any]] = d.get("undo_stack", [])
    for u in raw_undo:
        us.undo_stack.append(_dict_to_undo_entry(u))

    return us


def _dict_to_node_state(d: dict[str, Any]) -> NodeState:
    raw_dims = d.get("custom_dims", {})
    validated_dims: dict[str, int] = {}
    if isinstance(raw_dims, dict):
        for k, v in raw_dims.items():
            if isinstance(k, str) and isinstance(v, int) and 0 <= v <= 100:
                validated_dims[k] = v
    return NodeState(
        node_id=d["node_id"],
        status=NodeStatus(d.get("status", "NOT_STARTED")),
        score=int(d.get("score", 0)),
        evidence=d.get("evidence", []),
        custom_dims=validated_dims,
        updated_at=d.get("updated_at", ""),
    )


def _dict_to_history_entry(d: dict[str, Any]) -> HistoryEntry:
    return HistoryEntry(
        node_id=d["node_id"],
        field=d["field"],
        old_value=d["old_value"],
        new_value=d["new_value"],
        timestamp=d["timestamp"],
        description=d.get("description", ""),
    )


def _dict_to_undo_entry(d: dict[str, Any]) -> UndoEntry:
    raw_dims = d.get("previous_custom_dims", {})
    validated_dims: dict[str, int] = {}
    if isinstance(raw_dims, dict):
        for k, v in raw_dims.items():
            if isinstance(k, str) and isinstance(v, int):
                validated_dims[k] = v
    return UndoEntry(
        node_id=d["node_id"],
        action=d.get("action", "complete"),
        previous_status=d.get("previous_status", "NOT_STARTED"),
        previous_score=int(d.get("previous_score", 0)),
        previous_evidence=d.get("previous_evidence", []),
        previous_custom_dims=validated_dims,
        xp_earned=int(d.get("xp_earned", 0)),
        timestamp=d.get("timestamp", ""),
    )


# ── internal helpers ──────────────────────────────────────────────────


def _bump_updated_at(us: UserState) -> None:
    from los.common import utc_now_iso

    us.updated_at = utc_now_iso()


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


# ── Global UserState persistence ────────────────────────────────────────


def save_global_state(gus: GlobalUserState, path: str = GLOBAL_STATE_PATH) -> None:
    """Persist GlobalUserState to JSON."""
    _ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_global_user_state_to_dict(gus), f, indent=2, ensure_ascii=False)


def load_global_state(path: str = GLOBAL_STATE_PATH) -> GlobalUserState:
    """Load and return the GlobalUserState stored at *path*.

    Returns a *new*, empty GlobalUserState if the file does not exist.
    """
    if not os.path.isfile(path):
        return GlobalUserState()

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    return _dict_to_global_user_state(raw)


def _global_user_state_to_dict(gus: GlobalUserState) -> dict[str, Any]:
    return {
        "user_id": gus.user_id,
        "total_xp": gus.total_xp,
        "unlocked_achievements": gus.unlocked_achievements,
        "learning_history": [_history_entry_to_dict(h) for h in gus.learning_history],
        "created_at": gus.created_at,
        "updated_at": gus.updated_at,
        "schema_version": gus.schema_version,
    }


def _dict_to_global_user_state(d: dict[str, Any]) -> GlobalUserState:
    gus = GlobalUserState(
        user_id=d.get("user_id", "default"),
        total_xp=int(d.get("total_xp", 0)),
        unlocked_achievements=d.get("unlocked_achievements", []),
        created_at=d.get("created_at", ""),
        updated_at=d.get("updated_at", ""),
        schema_version=d.get("schema_version", CURRENT_SCHEMA_VERSION),
    )
    raw_hist: list[dict[str, Any]] = d.get("learning_history", [])
    for h in raw_hist:
        gus.learning_history.append(_dict_to_history_entry(h))
    return gus
