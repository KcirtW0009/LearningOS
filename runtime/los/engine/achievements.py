"""Achievement Engine — achievement detection and tracking.

Defined by: ACH-001 (Phase 7)

Responsibilities:
  - Define achievement conditions
  - Detect achievement unlocks given UserState
  - Return newly earned vs already earned achievements
  - Priority-sort achievements (rare first)

Design:
  - Achievements are stateless calculations — no separate storage
  - "Already earned" is detected by checking which achievements
    would pass the current state
  - For v1.0, achievements are recomputed each time (no history tracking)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from los.engine.rules import evaluate_progress_rule

if TYPE_CHECKING:
    from los.state.models import UserState


@dataclass(frozen=True)
class Achievement:
    id: str
    name: str
    description: str
    icon: str = ""
    rule: dict = field(default_factory=dict)
    priority: int = 0


CORE_ACHIEVEMENTS: list[Achievement] = [
    Achievement(
        id="completionist",
        name="全知全能",
        description="任一图谱 100% 完成",
        icon="⬡",
        rule={"type": "percentage", "min": 100},
        priority=100,
    ),
    Achievement(
        id="master-mind",
        name="登峰造极",
        description="10个节点达Master",
        icon="★",
        rule={"type": "mastered_count", "min": 10},
        priority=95,
    ),
    Achievement(
        id="centurion",
        name="百战不殆",
        description="累计5000 XP",
        icon="⚔",
        rule={"type": "xp_gte", "min": 5000},
        priority=90,
    ),
    Achievement(
        id="streak-7",
        name="周而复始",
        description="连续7天学习",
        icon="🔥",
        rule={"type": "streak", "min": 7},
        priority=85,
    ),
    Achievement(
        id="streak-30",
        name="月度之星",
        description="连续30天学习",
        icon="📅",
        rule={"type": "streak", "min": 30},
        priority=80,
    ),
    Achievement(
        id="triple-crown",
        name="三冠王",
        description="完成3个图谱",
        icon="👑",
        rule={"type": "multi_graph", "min": 3},
        priority=75,
    ),
    Achievement(
        id="speed-runner",
        name="闪电战",
        description="24小时内完成3个节点",
        icon="⚡",
        rule={"type": "daily_completed", "min": 3, "hours": 24},
        priority=70,
    ),
    Achievement(
        id="sage",
        name="温故知新",
        description="复习节点达到20次",
        icon="🦉",
        rule={"type": "review_count", "min": 20},
        priority=65,
    ),
    Achievement(
        id="first-step",
        name="第一步",
        description="完成第1个节点",
        icon="👣",
        rule={"type": "completed_count", "min": 1},
        priority=10,
    ),
    Achievement(
        id="getting-started",
        name="入门者",
        description="完成5个节点",
        icon="🌱",
        rule={"type": "completed_count", "min": 5},
        priority=15,
    ),
    Achievement(
        id="halfway",
        name="半程已过",
        description="完成50%节点",
        icon="🏔",
        rule={"type": "percentage", "min": 50},
        priority=20,
    ),
    Achievement(
        id="perfectionist",
        name="精益求精",
        description="某个节点 score=10+",
        icon="🎯",
        rule={"type": "score_gte", "min": 10},
        priority=25,
    ),
    Achievement(
        id="xp-100",
        name="百点经验",
        description="100 XP",
        icon="💎",
        rule={"type": "xp_gte", "min": 100},
        priority=30,
    ),
    Achievement(
        id="xp-1000",
        name="千点经验",
        description="1000 XP",
        icon="💎+",
        rule={"type": "xp_gte", "min": 1000},
        priority=35,
    ),
    Achievement(
        id="explorer",
        name="探索者",
        description="加载所有初始图谱",
        icon="🧭",
        rule={"type": "explorer", "count": 3},
        priority=40,
    ),
    Achievement(
        id="night-owl",
        name="夜猫子",
        description="22:00-06:00完成节点",
        icon="🌙",
        rule={"type": "night_owl"},
        priority=45,
    ),
    Achievement(
        id="first-graph",
        name="初出茅庐",
        description="加载第1个图谱",
        icon="📖",
        rule={"type": "first_graph"},
        priority=50,
    ),
    Achievement(
        id="undo-user",
        name="悔棋大师",
        description="使用撤销功能",
        icon="↩",
        rule={"type": "undo_used"},
        priority=55,
    ),
    Achievement(
        id="onboarder",
        name="好好学习",
        description="完成新手教程",
        icon="🎓",
        rule={"type": "onboarded"},
        priority=5,
    ),
]


def check_achievements(
    state: UserState,
    achievements: list[Achievement] | None = None,
    global_state: dict | None = None,
) -> list[tuple[Achievement, bool]]:
    if achievements is None:
        achievements = CORE_ACHIEVEMENTS

    results: list[tuple[Achievement, bool]] = []
    for ach in achievements:
        passed, _ = evaluate_progress_rule(state, ach.rule, global_state)
        results.append((ach, passed))
    results.sort(key=lambda x: (not x[1], -x[0].priority))
    return results


def get_new_achievements(
    state: UserState,
    previously_earned: set[str] | None = None,
    achievements: list[Achievement] | None = None,
    global_state: dict | None = None,
) -> list[Achievement]:
    if previously_earned is None:
        previously_earned = set()
    if achievements is None:
        achievements = CORE_ACHIEVEMENTS

    newly_earned: list[Achievement] = []
    for ach in achievements:
        if ach.id in previously_earned:
            continue
        passed, _ = evaluate_progress_rule(state, ach.rule, global_state)
        if passed:
            newly_earned.append(ach)
    newly_earned.sort(key=lambda a: -a.priority)
    return newly_earned
