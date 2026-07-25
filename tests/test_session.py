"""Tests for Session Authority — Session, SessionStatus, SessionBinding."""

from __future__ import annotations

import uuid

import pytest

from los.session import Session, SessionBinding, SessionStatus, get_binding


# ── SessionStatus ──────────────────────────────────────────────────────────


class TestSessionStatus:
    def test_created_value(self) -> None:
        assert SessionStatus.CREATED == "CREATED"

    def test_bound_value(self) -> None:
        assert SessionStatus.BOUND == "BOUND"

    def test_only_two_states(self) -> None:
        """Phase 5 requires only CREATED and BOUND — no future states."""
        assert len(SessionStatus) == 2
        assert SessionStatus.CREATED in SessionStatus
        assert SessionStatus.BOUND in SessionStatus


# ── Session ────────────────────────────────────────────────────────────────


class TestSession:
    def test_default_values(self) -> None:
        s = Session(session_id="abc")
        assert s.session_id == "abc"
        assert s.user_id == "default"
        assert s.status == SessionStatus.CREATED
        assert s.created_at != ""
        assert s.last_active != ""

    def test_timestamps_are_iso8601(self) -> None:
        s = Session(session_id="t1")
        # ISO-8601 contains "T" separator
        assert "T" in s.created_at
        assert "T" in s.last_active

    def test_no_runtime_id_field(self) -> None:
        """Session MUST NOT store runtime_id — R1 revision."""
        s = Session(session_id="abc")
        assert not hasattr(s, "runtime_id")

    def test_custom_user_id(self) -> None:
        s = Session(session_id="x", user_id="alice")
        assert s.user_id == "alice"

    def test_session_is_dataclass(self) -> None:
        s = Session(session_id="s1")
        # dataclass repr includes field=value pattern
        assert "session_id='s1'" in repr(s)


# ── SessionBinding ─────────────────────────────────────────────────────────


class TestSessionBinding:
    def test_initial_state(self) -> None:
        b = SessionBinding()
        assert b.current_session is None
        assert b.current_runtime is None

    def test_bind_sets_references(self) -> None:
        b = SessionBinding()
        s = Session(session_id="s1")

        class FakeRuntime:
            runtime_id = "fake-001"

        r = FakeRuntime()

        b.bind(s, r)

        assert b.current_session is s
        assert b.current_runtime is r
        assert s.status == SessionStatus.BOUND

    def test_bind_overwrites_previous(self) -> None:
        b = SessionBinding()
        s1 = Session(session_id="first")
        s2 = Session(session_id="second")

        class FakeRuntime:
            pass

        r1 = FakeRuntime()
        r2 = FakeRuntime()

        b.bind(s1, r1)
        b.bind(s2, r2)

        assert b.current_session is s2
        assert b.current_runtime is r2
        assert s1.status == SessionStatus.BOUND  # unchanged after being replaced

    def test_unbind_clears_runtime(self) -> None:
        b = SessionBinding()
        s = Session(session_id="s1")

        class FakeRuntime:
            pass

        b.bind(s, FakeRuntime())
        b.unbind()

        assert b.current_runtime is None
        assert b.current_session is s  # session identity survives
        assert s.status == SessionStatus.CREATED

    def test_unbind_when_nothing_bound(self) -> None:
        b = SessionBinding()
        b.unbind()  # no error

        assert b.current_session is None
        assert b.current_runtime is None

    def test_no_expire_method(self) -> None:
        """SessionBinding MUST NOT have expire() — R2 revision."""
        b = SessionBinding()
        assert not hasattr(b, "expire")


# ── get_binding ────────────────────────────────────────────────────────────


class TestGetBinding:
    def test_returns_session_binding(self) -> None:
        binding = get_binding()
        assert isinstance(binding, SessionBinding)

    def test_is_singleton(self) -> None:
        b1 = get_binding()
        b2 = get_binding()
        assert b1 is b2


# ── Dependency direction ──────────────────────────────────────────────────


class TestDependencyDirection:
    def test_session_imports_no_runtime_directly(self) -> None:
        """Session module itself must not import RuntimeInstance at module level."""
        from los.session.session import Session as _S
        import sys

        # Session module's own globals should not contain RuntimeInstance
        session_mod = sys.modules.get("los.session.session")
        assert session_mod is not None
        assert "RuntimeInstance" not in dir(session_mod)

    def test_binding_only_imports_runtime_in_type_checking(self) -> None:
        """binding.py uses TYPE_CHECKING guard for RuntimeInstance."""
        import los.session.binding as _m
        # At runtime, RuntimeInstance should not be in the module's namespace
        assert "RuntimeInstance" not in dir(_m)
