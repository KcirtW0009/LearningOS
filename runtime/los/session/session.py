"""Session — user identity for one interactive session.

Defined by:
  - RS-003 Session Binding Model (Frozen)
  - Phase 5 Session Authority (Approved)

Owner:      Session Authority
Scope:      Process-lifetime only — never persisted
Statuses:   CREATED → BOUND

Session stores identity only.  Runtime reference is held by
SessionBinding, not the Session model itself — runtime identity
belongs exclusively to Runtime Authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from los.common import utc_now_iso


# ── SessionStatus ─────────────────────────────────────────────────────────


class SessionStatus(str, Enum):
    """Session binding state.

    CREATED  — session exists, no runtime bound
    BOUND    — session bound to a RuntimeInstance
    """

    CREATED = "CREATED"
    BOUND = "BOUND"


# ── Session ───────────────────────────────────────────────────────────────


@dataclass
class Session:
    """A user session bound to a RuntimeInstance.

    Owns:
        session_id   — unique identity (uuid4)
        user_id      — who is using this session
        status       — binding state (CREATED / BOUND)
        created_at   — ISO-8601 timestamp
        last_active  — ISO-8601 timestamp

    Does NOT own:
        runtime_id   — runtime identity belongs to Runtime Authority
        RuntimeInstance reference — held by SessionBinding, not Session
    """

    session_id: str
    user_id: str = "default"
    status: SessionStatus = SessionStatus.CREATED
    created_at: str = ""
    last_active: str = ""

    def __post_init__(self) -> None:
        now = utc_now_iso()
        if not self.created_at:
            self.created_at = now
        if not self.last_active:
            self.last_active = now
