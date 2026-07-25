"""test_storage_adapter — JSON persistence save/load round-trip."""
import sys
sys.path.insert(0, ".")

import os
import tempfile

from tests.utils import cleanup_state_file

from los.state.models import (
    UserState, NodeState, NodeStatus, HistoryEntry, CURRENT_SCHEMA_VERSION,
)
from los.storage.adapter import save, load, exists


print("=== test_storage_adapter ===")
print()

# Clean up before starting
cleanup_state_file()

# ── 1. Load non-existent file returns fresh UserState ────────────────
tmp = os.path.join(tempfile.mkdtemp(), "state.json")
us = load(tmp)
assert isinstance(us, UserState)
assert us.user_id == "default"
assert us.graph_id == ""
assert us.node_states == {}
assert not exists(tmp)
print("1. Load non-existent returns fresh UserState OK")

# ── 2. Save then load: data round-trips ─────────────────────────────
us2 = UserState(user_id="tester", graph_id="test-graph", graph_version="2.0")
us2.node_states["n1"] = NodeState(
    node_id="n1", status=NodeStatus.COMPLETED, score=85,
    evidence=["notes.txt"],
)
us2.node_states["n2"] = NodeState(
    node_id="n2", status=NodeStatus.IN_PROGRESS, score=40,
)
save(us2, tmp)
assert exists(tmp)

us_loaded = load(tmp)
assert us_loaded.user_id == "tester"
assert us_loaded.graph_id == "test-graph"
assert us_loaded.graph_version == "2.0"
print("2. Save/load round-trip user-level fields OK")

# ── 3. Node states serialized and deserialized correctly ────────────
assert "n1" in us_loaded.node_states
assert "n2" in us_loaded.node_states
ns1 = us_loaded.node_states["n1"]
assert ns1.node_id == "n1"
assert ns1.status == NodeStatus.COMPLETED
assert ns1.score == 85
print("3. Node states round-trip OK")

# ── 4. Evidence list serialization ──────────────────────────────────
assert ns1.evidence == ["notes.txt"]
ns2 = us_loaded.node_states["n2"]
assert ns2.evidence == []
print("4. Evidence list serialization OK")

# ── 5. schema_version field preserved ───────────────────────────────
assert us_loaded.schema_version == CURRENT_SCHEMA_VERSION
print(f"5. schema_version={us_loaded.schema_version} preserved OK")

# ── 6. History entries survive round-trip ───────────────────────────
us3 = UserState(user_id="hist-test")
us3.history.append(HistoryEntry(
    node_id="a", field="status",
    old_value="NOT_STARTED", new_value="COMPLETED",
    timestamp="2025-01-01T00:00:00",
))
save(us3, tmp)
us3_loaded = load(tmp)
assert len(us3_loaded.history) == 1
he = us3_loaded.history[0]
assert he.node_id == "a"
assert he.field == "status"
assert he.new_value == "COMPLETED"
assert he.timestamp == "2025-01-01T00:00:00"
print("6. History entries survive round-trip OK")

# ── 7. Orphaned node_ids preserved ──────────────────────────────────
us4 = UserState(user_id="orphan-test", graph_id="old-graph")
us4.node_states["orphan-node"] = NodeState(
    node_id="orphan-node", status=NodeStatus.COMPLETED, score=99,
)
save(us4, tmp)
us4_loaded = load(tmp)
assert "orphan-node" in us4_loaded.node_states
assert us4_loaded.node_states["orphan-node"].score == 99
print("7. Orphaned node_ids preserved OK")

# ── 8. Multiple NodeStates round-trip ───────────────────────────────
assert len(us_loaded.node_states) == 2
print("8. Multiple NodeStates count preserved OK")

# ── 9. created_at / updated_at round-trip ───────────────────────────
assert us_loaded.created_at != ""
assert us_loaded.updated_at != ""
print(f"9. created_at / updated_at round-trip OK")

# ══════════════════════════════════════════════════════════════════════
# Phase 4 — Manifest persistence (dict-based, no Runtime imports)
# ══════════════════════════════════════════════════════════════════════

from los.storage.adapter import (
    DEFAULT_MANIFEST_PATH,
    load_manifest,
    manifest_exists,
    save_manifest,
)

_manifest_tmp = tmp.replace("state-test", "manifest-test") + ".json"

# ── 10. Manifest round-trip preserves all fields ─────────────────────
data = {
    "runtime_id": "abc123",
    "graph_path": "graphs/example",
    "graph_id": "example-basics",
    "graph_version": "1.0.0",
    "created_at": "2025-07-01T00:00:00",
    "last_active": "2025-07-13T00:00:00",
}
save_manifest(data, _manifest_tmp)
loaded = load_manifest(_manifest_tmp)
assert loaded is not None
assert loaded["runtime_id"] == "abc123"
assert loaded["graph_path"] == "graphs/example"
assert loaded["graph_id"] == "example-basics"
assert loaded["graph_version"] == "1.0.0"
assert loaded["created_at"] == "2025-07-01T00:00:00"
assert loaded["last_active"] == "2025-07-13T00:00:00"
print("10. Manifest round-trip OK")

# ── 11. load_manifest() missing file returns None ────────────────────
assert load_manifest("data/__nonexistent_manifest__.json") is None
print("11. Missing manifest → None OK")

# ── 12. manifest_exists() ────────────────────────────────────────────
assert manifest_exists(_manifest_tmp) is True
assert manifest_exists("data/__nonexistent_manifest__.json") is False
print(f"12. manifest_exists: {manifest_exists(_manifest_tmp)}")

# ── 13. Manifest with extra keys preserved ───────────────────────────
data_extra = {"runtime_id": "x", "graph_path": "p", "extra": "keep-me"}
save_manifest(data_extra, _manifest_tmp)
loaded_extra = load_manifest(_manifest_tmp)
assert loaded_extra["extra"] == "keep-me"
print("13. Manifest extra keys preserved OK")

# Cleanup
if os.path.isfile(_manifest_tmp):
    os.remove(_manifest_tmp)

# ── Clean up temp file ──────────────────────────────────────────────
if os.path.isfile(tmp):
    os.remove(tmp)

cleanup_state_file()

print()
print("All tests passed.")
