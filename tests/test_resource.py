"""Phase 6 Resource Model Tests.

Tests:
  - Resource creation with all field variants
  - Resource validation (invalid type, empty uri)
  - Node with resources
  - Node without resources (backward compat)
  - LoadedGraph resource query via node.resources
  - ResourceIndex module integration
"""
print("=== Phase 6 Resource Model Tests ===\n")

# ── Test 1: Resource creation ──────────────────────────────────────
from los.graph.models import Resource

r = Resource(type="url", uri="https://git-scm.com", label="Git 官方文档")
assert r.type == "url"
assert r.uri == "https://git-scm.com"
assert r.label == "Git 官方文档"
print("1. Resource creation OK")

# ── Test 2: Resource without label ──────────────────────────────────
r = Resource(type="file", uri="./slides/git-intro.pdf")
assert r.label is None
print("2. Resource without label OK")

# ── Test 3: Resource markdown type ──────────────────────────────────
r = Resource(type="markdown", uri="# 这是一段 Markdown 内容")
assert r.type == "markdown"
print("3. Resource markdown type OK")

# ── Test 4: Invalid resource type ───────────────────────────────────
try:
    Resource(type="invalid", uri="http://example.com")
    assert False, "Should have raised ValueError"
except ValueError as e:
    assert "Unknown Resource type" in str(e)
print("4. Invalid resource type → ValueError OK")

# ── Test 5: Empty uri ───────────────────────────────────────────────
try:
    Resource(type="url", uri="")
    assert False, "Should have raised ValueError"
except ValueError:
    pass
print("5. Empty uri → ValueError OK")

# ── Test 6: Node with resources ─────────────────────────────────────
from los.graph.models import Node

node = Node(
    id="test-01",
    title="测试节点",
    description="一个带资源的测试节点",
    resources=[
        Resource(type="url", uri="https://example.com", label="示例链接"),
        Resource(type="file", uri="./notes.md"),
    ],
)
assert len(node.resources) == 2
assert node.resources[0].label == "示例链接"
print("6. Node with resources OK")

# ── Test 7: Node without resources (backward compat) ─────────────────
node = Node(id="test-02", title="无资源节点", description="没有 resources 字段")
assert len(node.resources) == 0
print("7. Node without resources (backward compat) OK")

# ── Test 8: LoadedGraph get_node carries resources ──────────────────
from los.graph.loader import load_graph_package

graph = load_graph_package("graphs/git-fundamentals")
git01 = graph.get_node("git-01")
assert git01 is not None
assert len(git01.resources) == 1
assert git01.resources[0].type == "url"
assert "Pro Git" in git01.resources[0].label
print(f"8. LoadedGraph git-01 has {len(git01.resources)} resource(s) OK")

# ── Test 9: Node with no resources in graph ─────────────────────────
git03 = graph.get_node("git-03")
assert git03 is not None
assert len(git03.resources) == 0  # no resources defined in YAML
print("9. Node without resources → empty list OK")

# ── Test 10: ResourceIndex integration ──────────────────────────────
from los.resource import get_resources, get_resources_by_type

res = get_resources(graph, "git-02")
assert len(res) == 2
assert res[0].type == "url"
print(f"10. get_resources(git-02) → {len(res)} items OK")

# ── Test 11: Filter by type ─────────────────────────────────────────
urls = get_resources_by_type(graph, "git-02", "url")
assert len(urls) == 2
assert all(r.type == "url" for r in urls)
print(f"11. get_resources_by_type(git-02, url) → {len(urls)} items OK")

# ── Test 12: Unknown node → empty list ──────────────────────────────
assert get_resources(graph, "no-such-node") == []
print("12. Unknown node → empty list OK")

# ── Test 13: Unused type filter → empty ─────────────────────────────
assert get_resources_by_type(graph, "git-01", "file") == []
print("13. No matching type → empty list OK")

# ── Test 14: RuntimeInstance.get_node_detail includes resources ─────
from los.runtime.runtime_instance import RuntimeInstance

ri = RuntimeInstance.load("graphs/git-fundamentals")
detail = ri.get_node_detail("git-01")
assert detail is not None
assert "resources" in detail
assert len(detail["resources"]) == 1
assert detail["resources"][0]["type"] == "url"
print(f"14. get_node_detail includes resources: {len(detail['resources'])} item(s) OK")

# ── Test 15: CLI input/output stable (no _runtime global) ───────────
import los.cli.main as cli
assert not hasattr(cli, '_runtime'), "CLI must not have _runtime global"
assert hasattr(cli, '_binding'), "CLI must have _binding"
print("15. CLI architecture check OK")

print("\nAll tests passed.")
