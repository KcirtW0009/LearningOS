"""SessionBinding — process-lifetime Session → Runtime binding.

Defined by:
  - RS-003 Session Binding Model (Frozen)
  - Phase 5 Session Authority (Approved)

Responsibility:
    Hold the current Session identity and its bound RuntimeInstance
    handle for the lifetime of one CLI process.

    Binding is never serialized or persisted — it exists only in
    process memory.

Dependencies:
    los.runtime.runtime_instance (type annotation only, downward direction)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from los.session.session import Session, SessionStatus

if TYPE_CHECKING:
    from los.runtime.runtime_instance import RuntimeInstance


# ── SessionBinding ────────────────────────────────────────────────────────


class SessionBinding:
    """Manages the current Session → Runtime binding.

    Holds the process-lifetime reference to the active session and
    its bound RuntimeInstance.  Provides the access point for CLI
    and future consumers.
    """

    def __init__(self) -> None:
        self._session: Session | None = None
        self._runtime: RuntimeInstance | None = None

    # ── public properties ─────────────────────────────────────────────

    @property
    def current_session(self) -> Session | None:
        """The active Session, or None if no session has been created."""
        return self._session

    @property
    def current_runtime(self) -> RuntimeInstance | None:
        """The bound RuntimeInstance, or None if not bound."""
        return self._runtime

    # ── public methods ────────────────────────────────────────────────

    def bind(self, session: Session, runtime: RuntimeInstance) -> None:
        """Bind *session* to *runtime*.

        Sets session status → BOUND and stores both references.
        Overwrites any previous binding — old session is simply
        replaced (matching the existing _runtime-overwrite behaviour).
        """
        session.status = SessionStatus.BOUND
        self._session = session
        self._runtime = runtime

    def unbind(self) -> None:
        """Release the runtime binding.

        Resets session status → CREATED and clears the runtime
        reference.  The session identity survives for potential
        re-bind.
        """
        if self._session is not None:
            self._session.status = SessionStatus.CREATED
        self._runtime = None


# ── module-level default singleton ────────────────────────────────────────


_default_binding = SessionBinding()


def get_binding() -> SessionBinding:
    """Return the module-level default SessionBinding singleton.

    All CLI handlers share this one binding.  Future multi-session
    support would replace this with a registry.
    """
    return _default_binding
