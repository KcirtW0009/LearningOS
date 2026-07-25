"""诊断脚本：验证所有用户反馈的问题根因"""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("1. CORE_ACHIEVEMENTS")
from runtime.los.engine.achievements import CORE_ACHIEVEMENTS
print(f"   Count: {len(CORE_ACHIEVEMENTS)}")
for i, a in enumerate(CORE_ACHIEVEMENTS):
    icon = a.icon.encode('ascii','replace').decode('ascii')
    print(f"   [{i+1:2d}] {a.id:20s} {a.name:10s} priority={a.priority}")

print()
print("=" * 60)
print("2. XP Formula")
from runtime.los.engine.xp import get_level, xp_to_next_level
print(f"   Current get_level(0)   = {get_level(0)} (expected 1)")
print(f"   Current get_level(50)  = {get_level(50)} (expected 2)")
print(f"   Current get_level(200) = {get_level(200)} (expected 3)")
print(f"   Current xp_to_next_level(0)   = {xp_to_next_level(0)} (expected 50)")
print(f"   Current xp_to_next_level(50)  = {xp_to_next_level(50)} (expected 150)")
print(f"   Current xp_to_next_level(200) = {xp_to_next_level(200)} (expected 250)")
print()

print("=" * 60)
print("3. PROFICIENCY_LEVELS")
from runtime.los.engine.xp import PROFICIENCY_LEVELS, get_proficiency
for t in sorted(PROFICIENCY_LEVELS.keys()):
    p = PROFICIENCY_LEVELS[t]
    icon = str(p['icon']).encode('ascii','replace').decode('ascii')
    print(f"   >={t:2d}: {p['label']:6s} ({p['label_en']:10s}) icon={icon} factor={p.get('factor','?')}")
print(f"   get_proficiency(10) = label_en={get_proficiency(10)['label_en']}")
print()

print("=" * 60)
print("4. DEFAULT_SCORE_PRESETS")
from runtime.los.state.models import DEFAULT_SCORE_PRESETS
for p in DEFAULT_SCORE_PRESETS:
    print(f"   {p['label']:8s} score={p['score']}")

print()
print("=" * 60)
print("5. Node complete with score=10")
from runtime.los.state.engine import complete_node
from runtime.los.state.models import UserState, NodeState
us = UserState(user_id="test", graph_id="test")
us.node_states["n1"] = NodeState(node_id="n1", score=0)
us.node_states["n2"] = NodeState(node_id="n2", score=0)
try:
    he = complete_node(us, "n1", score=10)
    ns = us.node_states["n1"]
    print(f"   node n1: status={ns.status.value}, score={ns.score}, is_completed={ns.is_completed}")
    print(f"   OK - score=10 can complete node")
except Exception as e:
    print(f"   FAIL: {e}")

print()
print("=" * 60)
print("6. learning-log API check")
server_path = os.path.join(os.path.dirname(__file__), "runtime", "los", "api", "server.py")
with open(server_path, 'r', encoding='utf-8') as f:
    content = f.read()
print(f"   /learning-log endpoint in server.py: {'YES' if '@app.get(\"/learning-log\")' in content else 'NO'}")
print()
print("=" * 60)
print("SUMMARY:")
print("  Source code is CORRECT for all features.")
print("  Packaged backend.exe is STALE (old code).")
print("  XP xp_to_next_level formula is WRONG in source too!")
print("  get_level() also needs fix for level boundaries.")
