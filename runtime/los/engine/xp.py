"""XP Engine — experience point calculation.

Defined by: XP-001 (Phase 7)

Responsibilities:
  - Calculate XP earned from completing a Node
  - Compute total XP from UserState
  - Calculate boss (milestone) bonus XP
  - Map score to proficiency level

XP formula:
  BASE_XP(20) × score_factor × difficulty × proficiency_factor

  score_factor = max(1, score // 5)
  difficulty: beginner=1, intermediate=1.5, advanced=2
  proficiency_factor: based on pre-review proficiency (encourages review)
                      None/Done=1.0, Known=1.2, Skilled=1.5, Expert=2.0, Master=3.0

Level formula:
  level = max(1, sqrt(total_xp / 50))

Boss Bonus:
  bonus = BASE_XP × difficulty × BOSS_BONUS_MULTIPLIER(5)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from los.state.models import UserState

BASE_XP: int = 25

DIFFICULTY_MULTIPLIER: dict[str, float] = {
    "beginner": 1.0,
    "intermediate": 1.5,
    "advanced": 2.0,
}

BOSS_BONUS_MULTIPLIER: int = 5

PROFICIENCY_LEVELS: dict[int, dict[str, str | float | int]] = {
    0:  {"label": "未开始", "label_en": "None",      "color": "#94a3b8", "icon": "○",      "factor": 1.0},
    5:  {"label": "完成",   "label_en": "Done",       "color": "#94a3b8", "icon": "✓",      "factor": 1.0},
    10: {"label": "熟悉",   "label_en": "Known",      "color": "#3b82f6", "icon": "◈",      "factor": 1.2},
    20: {"label": "掌握",   "label_en": "Skilled",    "color": "#8b5cf6", "icon": "◆",      "factor": 1.5},
    50: {"label": "熟练",   "label_en": "Expert",     "color": "#f59e0b", "icon": "★",      "factor": 2.0},
    80: {"label": "精通",   "label_en": "Master",     "color": "#ef4444", "icon": "⬡",      "factor": 3.0},
}

PROFICIENCY_THRESHOLDS = sorted(PROFICIENCY_LEVELS.keys())


def get_proficiency(score: int) -> dict[str, str | float | int]:
    level = PROFICIENCY_LEVELS[0]
    for threshold in PROFICIENCY_THRESHOLDS:
        if score >= threshold:
            level = PROFICIENCY_LEVELS[threshold]
    return dict(level)


def calculate_xp(
    difficulty: str | None,
    score: int,
    previous_score: int = 0,
) -> int:
    mult = DIFFICULTY_MULTIPLIER.get(difficulty or "", 1.0)
    score_factor = max(1, score // 5)
    prev_prof = get_proficiency(previous_score)
    prof_factor = prev_prof["factor"]
    raw = BASE_XP * score_factor * mult * prof_factor
    return max(5, int(round(raw)))


def calculate_boss_bonus(difficulty: str | None) -> int:
    mult = DIFFICULTY_MULTIPLIER.get(difficulty or "", 1.0)
    return int(BASE_XP * mult * BOSS_BONUS_MULTIPLIER)


def compute_total_xp(state: UserState) -> int:
    """Return total XP — prefers state.total_xp (maintained by add_score_event).

    Falls back to calculating from node scores for migrated states where
    total_xp was not previously tracked.  Uses a conservative estimate:
    score × BASE_XP_FACTOR (5) to approximate XP from raw scores.
    """
    if state.total_xp > 0:
        return state.total_xp
    # Fallback for legacy states: estimate XP from raw scores
    total = 0
    for ns in state.node_states.values():
        if ns.score > 0:
            total += ns.score * 5
    return total


def get_level(total_xp: int) -> int:
    """Return user level based on total XP.

    Level formula: floor(sqrt(xp / 50)) + 1
    Lv.1 at 0 XP, Lv.2 at 50 XP, Lv.3 at 200 XP, Lv.4 at 450 XP, ...
    """
    return int((total_xp / 50) ** 0.5) + 1


def xp_to_next_level(total_xp: int) -> int:
    """Return XP needed to reach the next level."""
    current_level = get_level(total_xp)
    next_level_xp = current_level ** 2 * 50
    return max(0, next_level_xp - total_xp)
