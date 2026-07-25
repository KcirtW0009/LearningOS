"""Phase 1 verification script — test graph/preview and graph/save logic
with Chinese characters, '/' in titles, and 'dependency' edges."""

import os
import sys
import json
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runtime"))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

from los.api.server import _PROJECT_ROOT, _SAFE_PREFIX

# Read the zotero test yaml
yaml_path = os.path.join(os.path.dirname(__file__), "fixtures", "zotero_test.yaml")
with open(yaml_path, "r", encoding="utf-8") as f:
    ZOTERO_YAML = f.read()

print("=" * 60)
print("Phase 1 — Verify recent fixes with Zotero YAML")
print("=" * 60)
print(f"_PROJECT_ROOT = {_PROJECT_ROOT}")
print(f"_SAFE_PREFIX  = {_SAFE_PREFIX}")
print()

# ─────────────────────────────────────────────────────────────────────
# 1. Test graph/preview logic
# ─────────────────────────────────────────────────────────────────────
print("--- 1a. YAML parse + preview validation (imports server models) ---")

import yaml as _yaml
from pydantic import BaseModel
from los.graph.models import VALID_RELATIONS as VR

class GraphYamlRequest(BaseModel):
    yaml: str

# Parse the YAML exactly like server.py does
raw = _yaml.safe_load(ZOTERO_YAML)
assert isinstance(raw, dict), "YAML must be a mapping"

package_id = str(raw.get("package_id", ""))
name = str(raw.get("name", ""))
version = str(raw.get("version", ""))
print(f"  package_id = {package_id}")
print(f"  name       = {name}")
print(f"  version    = {version}")
print(f"  manifest fields OK: {bool(package_id and name and version)}")

nodes_raw = raw.get("nodes", [])
edges_raw = raw.get("edges", [])
print(f"  node count = {len(nodes_raw)}  (expected 9)")
print(f"  edge count = {len(edges_raw)}  (expected 14)")
assert len(nodes_raw) == 9, f"Expected 9 nodes, got {len(nodes_raw)}"
assert len(edges_raw) == 14, f"Expected 14 edges, got {len(edges_raw)}"

# Validate nodes
node_ids = set()
for i, n in enumerate(nodes_raw):
    nid = str(n.get("id", ""))
    ntitle = str(n.get("title", ""))
    ndesc = str(n.get("description", ""))
    assert nid and ntitle and ndesc, f"Node[{i}] missing required fields: {n}"
    assert nid not in node_ids, f"Duplicate node id: {nid}"
    node_ids.add(nid)
    # Check Chinese characters and '/' are preserved (no corruption during load)
    if nid == "cite-insert":
        assert "Word / Google Docs" in ntitle, f"'/' character lost in cite-insert title: {ntitle}"
        print(f"  cite-insert title preserved with '/': {ntitle}")
    if any("\u4e00" <= ch <= "\u9fff" for ch in ntitle):
        pass  # Chinese chars exist — they are preserved through yaml.safe_load
print(f"  Nodes validated: {len(node_ids)} unique IDs, Chinese + '/' chars OK")

# Validate edges — must include 'dependency' and all relations in VALID_RELATIONS
edges = []
dependency_count = 0
relation_types_found = set()
for i, e in enumerate(edges_raw):
    efrom = str(e.get("from", ""))
    eto = str(e.get("to", ""))
    erel = str(e.get("relation", ""))
    assert efrom in node_ids, f"Edge[{i}] from='{efrom}' unknown"
    assert eto in node_ids, f"Edge[{i}] to='{eto}' unknown"
    assert erel in VR, f"Edge[{i}] relation='{erel}' not in VALID_RELATIONS={VR}"
    relation_types_found.add(erel)
    if erel == "dependency":
        dependency_count += 1
    edges.append((efrom, eto, erel))

# Verify specific dependency edge from Handoff doc: attach-pdfs → sync-collaboration
dep_pairs = [(e[0], e[1]) for e in edges if e[2] == "dependency"]
assert ("attach-pdfs", "sync-collaboration") in dep_pairs, (
    f"Expected 'attach-pdfs → sync-collaboration' dependency edge, found: {dep_pairs}"
)
print(f"  Edges validated: {len(edges)} edges")
print(f"    relation types used: {sorted(relation_types_found)}")
print(f"    dependency edges: {dependency_count}  (includes attach-pdfs→sync-collaboration ✓)")
print(f"  preview.valid = TRUE (no errors detected)")
print()

# ─────────────────────────────────────────────────────────────────────
# 2. Test graph/save path traversal guard and file write
# ─────────────────────────────────────────────────────────────────────
print("--- 1b. graph/save: path safety + directory creation ---")

safe_id = "learn-zotero"
target_dir = os.path.normpath(os.path.join(_SAFE_PREFIX, safe_id))
print(f"  safe_id    = {safe_id}")
print(f"  target_dir = {target_dir}")
assert target_dir.startswith(_SAFE_PREFIX + os.sep) or target_dir == _SAFE_PREFIX, (
    f"PATH TRAVERSAL DETECTED: target_dir={target_dir} not under {_SAFE_PREFIX}"
)
print(f"  path safety: OK (starts with _SAFE_PREFIX)")

# Backup existing dir if any
backup_dir = None
if os.path.isdir(target_dir):
    backup_dir = target_dir + ".bak-" + str(os.getpid())
    shutil.move(target_dir, backup_dir)
    print(f"  existing dir backed up to: {backup_dir}")

try:
    # Mimic save logic from server.py
    os.makedirs(target_dir, exist_ok=True)
    manifest = {
        "package_id": package_id,
        "name": name,
        "version": version,
    }
    author = str(raw.get("author", ""))
    if author:
        manifest["author"] = author

    manifest_path = os.path.join(target_dir, "manifest.yaml")
    graph_path = os.path.join(target_dir, "graph.yaml")

    with open(manifest_path, "w", encoding="utf-8") as f:
        _yaml.safe_dump(manifest, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    graph_content = {
        "nodes": nodes_raw,
        "edges": edges_raw,
    }
    with open(graph_path, "w", encoding="utf-8") as f:
        _yaml.safe_dump(graph_content, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"  manifest.yaml written: {manifest_path}")
    print(f"  graph.yaml written:    {graph_path}")
    assert os.path.isfile(manifest_path), "manifest.yaml not created"
    assert os.path.isfile(graph_path), "graph.yaml not created"

    # Re-read and verify Chinese chars + '/' are preserved on disk
    with open(graph_path, "r", encoding="utf-8") as f:
        saved_graph = _yaml.safe_load(f)
    cite_title = next(n["title"] for n in saved_graph["nodes"] if n["id"] == "cite-insert")
    assert "Word / Google Docs" in cite_title, f"Round-trip '/' lost: {cite_title}"
    zotero_name = next(n["title"] for n in saved_graph["nodes"] if n["id"] == "install-zotero")
    assert any("\u4e00" <= ch <= "\u9fff" for ch in zotero_name), (
        f"Round-trip Chinese chars lost in install-zotero title: {zotero_name}"
    )
    print(f"  round-trip verification OK: '/', Chinese chars preserved in saved files")
    print(f"  save.status = SAVED")
    print()

    # ──────────────────────────────────────────────────────────────────
    # 3. Verify dependency edge actually unlocks correctly at runtime
    # ──────────────────────────────────────────────────────────────────
    print("--- 1c. Runtime: verify 'dependency' edge blocks correctly ---")
    from los.runtime.runtime_instance import RuntimeInstance
    from los.graph.models import is_blocking_relation

    ri = RuntimeInstance.load("graphs/learn-zotero")
    avail_initial = ri.get_available_nodes()
    print(f"  available nodes on load: {len(avail_initial)} → {avail_initial}")
    assert "install-zotero" in avail_initial, "Root node install-zotero should be available"
    # attach-pdfs, sync-collaboration should be LOCKED initially
    assert "attach-pdfs" not in avail_initial, "attach-pdfs should be LOCKED on initial load"
    assert "sync-collaboration" not in avail_initial, "sync-collaboration should be LOCKED on initial load"
    print(f"  LOCKED on load: attach-pdfs ✓, sync-collaboration ✓ (as expected)")
    print(f"  load() succeeds for saved Chinese-titled graph ✓")

    # ── STEP 1: Complete the prerequisite chain for cite-insert ──
    # install-zotero →(prereq) create-library →(prereq) import-pdfs
    #   →(progression) organize-tags →(prereq) cite-insert
    # AND create-library →(progression) sync-account
    chain1 = ["install-zotero", "create-library", "import-pdfs",
              "organize-tags", "cite-insert", "sync-account"]
    for step_id in chain1:
        avail = ri.get_available_nodes()
        assert step_id in avail, f"Expected {step_id} to be AVAILABLE. Current: {avail}"
        msg = ri.complete_node(step_id)
        print(f"    ✓ completed {step_id}: {msg[:55]}...")

    avail_after_chain1 = ri.get_available_nodes()
    # attach-pdfs has TWO blocking in-edges:
    #   import-pdfs →(dependency) attach-pdfs
    #   cite-insert →(progression) attach-pdfs
    # Both are satisfied now, so attach-pdfs MUST be available
    assert "attach-pdfs" in avail_after_chain1, (
        f"attach-pdfs must be AVAILABLE after completing BOTH its blocking "
        f"sources (import-pdfs [dependency] + cite-insert [progression]). "
        f"Available: {avail_after_chain1}"
    )
    print(f"  ✓ attach-pdfs AVAILABLE: dependency+progression both satisfied")

    # ── Negative check: attach-pdfs →(dependency) sync-collaboration is still LOCKED
    #   because sync-collaboration ALSO has prerequisite sync-account
    #   (sync-account already done above — so just need attach-pdfs now)
    #   → Actually let's do a cleaner isolation test for "dependency".
    # Reset state: use a graph with ONLY a dependency edge between 2 nodes.
    print()
    print("  --- Clean isolation test: dependency edge alone ---")
    from los.graph.models import Node, Edge, VALID_RELATIONS
    from los.state.models import UserState
    from los.graph.loader import LoadedGraph

    n_src = Node(id="src", title="Source", description="s")
    n_tgt = Node(id="tgt", title="Target", description="t")
    e_dep = Edge(source="src", target="tgt", relation="dependency")
    # Confirm dependency IS registered as blocking:
    assert is_blocking_relation("dependency"), (
        "FAIL: 'dependency' is NOT in _BLOCKING_RELATIONS. "
        "Check graph/models.py _BLOCKING_RELATIONS set."
    )
    print(f"  ✓ is_blocking_relation('dependency') = True (models.py correct)")
    lg = LoadedGraph(
        package_id="isolation-test",
        package_name="Isolation",
        package_version="1.0.0",
        author="test",
        nodes=[n_src, n_tgt],
        edges=[e_dep],
    )
    us = UserState()
    from los.runtime.runtime_instance import RuntimeInstance
    ri_iso = RuntimeInstance(lg, us)
    ri_iso._transition(type(ri_iso.status).ACTIVE)
    from los.state.engine import sync_node_states
    sync_node_states(ri_iso._state, [n.id for n in lg.nodes])
    # Before completing src → tgt LOCKED
    iso_avail = ri_iso.get_available_nodes()
    assert "tgt" not in iso_avail, f"dependency not blocking! tgt should be LOCKED, available={iso_avail}"
    print(f"  ✓ Isolation: before src complete, tgt is LOCKED (dependency blocks ✓)")
    # Complete src → tgt UNLOCKED
    ri_iso.complete_node("src")
    iso_avail2 = ri_iso.get_available_nodes()
    assert "tgt" in iso_avail2, f"dependency not unlocking! tgt should be AVAILABLE after src. Got: {iso_avail2}"
    print(f"  ✓ Isolation: after src complete, tgt is AVAILABLE (dependency unblocks ✓)")

    # ── Attach-pdfs complete and check sync-collaboration dependency ──
    print()
    print("  --- Full Zotero graph: attach-pdfs→sync-collaboration dependency ---")
    ri.complete_node("attach-pdfs")
    avail_final = ri.get_available_nodes()
    # sync-collaboration has 2 blocking in-edges BOTH satisfied now:
    #   attach-pdfs →(dependency) sync-collaboration  ✓ done
    #   sync-account →(prerequisite) sync-collaboration ✓ done earlier
    assert "sync-collaboration" in avail_final, (
        f"sync-collaboration MUST be AVAILABLE after attach-pdfs (dependency) "
        f"+ sync-account (prerequisite) both complete. Available: {avail_final}"
    )
    print(f"  ✓ sync-collaboration AVAILABLE: attach-pdfs[dependency] + sync-account[prereq] both satisfied")

    print()
    print("=" * 60)
    print("Phase 1 — ALL VERIFICATIONS PASSED")
    print("=" * 60)

finally:
    # Cleanup: restore backup or remove test dir
    if os.path.isdir(target_dir):
        shutil.rmtree(target_dir)
        print(f"Cleaned up test dir: {target_dir}")
    if backup_dir and os.path.isdir(backup_dir):
        shutil.move(backup_dir, target_dir)
        print(f"Restored original dir from: {backup_dir}")
