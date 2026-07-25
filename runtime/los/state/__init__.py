"""State module — manages user learning progress.

Exports from:
  - models  — NodeState, UserState, NodeStatus, HistoryEntry
  - engine  — sync_node_states, complete_node, start_node, get_progress, get_node_status, StateHandle
"""

from los.state.engine import (
    StateHandle,
    complete_node,
    get_node_status,
    get_progress,
    start_node,
    sync_node_states,
)
from los.state.models import (
    CURRENT_SCHEMA_VERSION,
    HistoryEntry,
    NodeState,
    NodeStatus,
    UserState,
)

__all__ = [
    # models
    "NodeStatus",
    "NodeState",
    "HistoryEntry",
    "UserState",
    "CURRENT_SCHEMA_VERSION",
    # engine
    "sync_node_states",
    "complete_node",
    "start_node",
    "get_progress",
    "get_node_status",
    "StateHandle",
]
