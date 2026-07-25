"""Phase 11: Comprehensive API Integration Test."""
import json, urllib.request, sys, os

BASE = "http://localhost:8000"
passed = 0
failed = 0

def GET(path):
    r = urllib.request.urlopen(f"{BASE}{path}")
    return json.loads(r.read())

def POST(path, data=None):
    body = json.dumps(data or {}).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=body,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    return json.loads(urllib.request.urlopen(req).read())

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}" + (f" — {detail}" if detail else ""))
    else:
        failed += 1
        print(f"  [FAIL] {name}" + (f" — {detail}" if detail else ""))

print("=" * 60)
print("  LearningOS API Integration Test Suite")
print("=" * 60)

# ═══ 1. Health ═══
print("\n── 1. Health Check ──")
check("GET /health returns ok", GET("/health")["status"] == "ok")

# ═══ 2. Load Graph ═══
print("\n── 2. Graph Load ──")
r = POST("/graph/load", {"path": "graphs/git-fundamentals"})
check("POST /graph/load returns loaded", r["status"] == "loaded")
check("Package name correct", r["package_name"] == "Git 基础与实战")
check("Node count 15", r["node_count"] == 15)
check("Edge count 17", r["edge_count"] == 17)

# ═══ 3. Graph Info ═══
print("\n── 3. Graph Info ──")
info = GET("/graph/info")
check("GET /graph/info node_count", info["node_count"] == 15)
check("Package version", info["package_version"] == "1.0.0")

# ═══ 4. Node List ═══
print("\n── 4. Node List ──")
nodes = GET("/nodes")
check("Available nodes non-empty", len(nodes) > 0, f"{len(nodes)} nodes")
check("git-01 is available", "git-01" in nodes)

# ═══ 5. Node Detail ═══
print("\n── 5. Node Detail ──")
detail = GET("/nodes/git-01")
check("Node id correct", detail["id"] == "git-01")
check("Has title", bool(detail["title"]))
check("Has description", bool(detail["description"]))
check("Has difficulty", bool(detail["difficulty"]))
check("Has resources list", isinstance(detail.get("resources"), list))
check("git-01 has 1 resource", len(detail["resources"]) == 1)

# ═══ 6. Complete Node ═══
print("\n── 6. Complete Node ──")
r = POST("/nodes/git-01/complete", {"score": 8})
check("Complete git-01 success", "Completed" in r.get("message", ""))
check("Message contains XP", "+" in r.get("message", ""))

# Complete more nodes to test unlock chain
POST("/nodes/git-02/complete", {"score": 10})
POST("/nodes/git-03/complete", {"score": 7})
POST("/nodes/git-11/complete", {"score": 9})
nodes2 = GET("/nodes")
check("More nodes unlocked", len(nodes2) > len(nodes), f"now {len(nodes2)} available")

# ═══ 7. Status ═══
print("\n── 7. Progress Status ──")
st = GET("/status")
check("Completed count correct", st["completed"] == 4)
check("Total is 15", st["total"] == 15)
check("Percentage correct", isinstance(st["percentage"], (int, float)) and st["percentage"] > 0, f"got {st['percentage']}")

# ═══ 8. XP ═══
print("\n── 8. XP ──")
xp = GET("/xp")
check("XP > 0 after completing nodes", xp["total_xp"] > 0, f"XP={xp['total_xp']}")
check("Level >= 1", xp["level"] >= 1)
check("Has xp_to_next_level", isinstance(xp.get("xp_to_next_level"), int))

# ═══ 9. Achievements ═══
print("\n── 9. Achievements ──")
ach = GET("/achievements")
check("Has earned achievements", len(ach["earned"]) > 0, f"{len(ach['earned'])} earned")
check("Has locked achievements", len(ach["locked"]) > 0, f"{len(ach['locked'])} locked")
earned_ids = [a["id"] for a in ach["earned"]]
check("First-step earned", "first-step" in earned_ids)
check("Total achievements = 8", len(ach["earned"]) + len(ach["locked"]) == 8)

# ═══ 10. Recommendations ═══
print("\n── 10. Recommendations ──")
recs = GET("/recommendations?strategy=next_available")
check("Strategy is next_available", recs["strategy"] == "next_available")
check("Has recommendations", len(recs["recommendations"]) > 0)
check("Recommendations are sorted (beginner first)", "git-" in recs["recommendations"][0])

# ═══ 11. Error handling ═══
print("\n── 11. Error Handling ──")
try:
    GET("/nodes/no-such-node")
    check("404 for unknown node", False)
except urllib.error.HTTPError as e:
    check("404 for unknown node", e.code == 404, f"got {e.code}")

try:
    POST("/nodes/no-such-node/complete", {"score": 10})
    check("400 for bad complete", False)
except urllib.error.HTTPError as e:
    check("400 for bad complete", e.code == 400, f"got {e.code}")

# ═══ Summary ═══
print("\n" + "=" * 60)
total = passed + failed
print(f"  Results: {passed}/{total} passed")
if failed:
    print(f"  FAILED: {failed} tests")
    sys.exit(1)
else:
    print("  ALL TESTS PASSED")
print("=" * 60)
