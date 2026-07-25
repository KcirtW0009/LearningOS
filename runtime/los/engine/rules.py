"""Rule Engine — predicate-based unlock conditions.

Defined by: RL-001 (Phase 7)

Responsibilities:
  - Evaluate rule predicates against UserState
  - Extend Resolver with score/XP-based unlock conditions

Does NOT own:
  - Structural prerequisite resolution (Resolver owns this)
  - State mutation
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from los.state.models import UserState


def evaluate_progress_rule(
    state: UserState,
    rule: dict,
    global_state: dict | None = None,
) -> tuple[bool, str]:
    """Evaluate a progress-based rule predicate against UserState.

    Supported rules:
      {"type": "completed_count", "min": N}  → completed >= N
      {"type": "percentage", "min": N}       → completion % >= N (on total nodes in state)
      {"type": "score_gte", "node_id": id, "min": N}  → specific node score >= N
      {"type": "xp_gte", "min": N}           → total_xp >= N
      {"type": "mastered_count", "min": N}  → mastered nodes >= N
      {"type": "multi_graph", "min": N}      → completed graphs >= N (needs global_state)
      {"type": "explorer", "count": N}       → loaded graphs >= N (needs global_state)
      {"type": "speed_run", "hours": N}      → all nodes finished within N hours
      {"type": "review_count", "min": N}     → total review events >= N

    Args:
        state: Current graph's UserState
        global_state: Optional aggregated cross-graph stats
                      {"graphs_completed": int, "graphs_loaded": int, "total_xp": int}

    Returns:
        (passed, reason_string)
    """
    rule_type = rule.get("type", "")
    minimum = rule.get("min", 0)

    if rule_type == "completed_count":
        if global_state:
            completed = global_state.get("total_completed_count", 0)
        else:
            completed = _count_by_status(state, {"COMPLETED", "MASTERED"})
        ok = completed >= minimum
        return ok, (
            f"completed {completed}/{minimum}"
            if ok
            else f"need {minimum} completed, have {completed}"
        )

    if rule_type == "percentage":
        if global_state:
            total = global_state.get("total_nodes", 0)
            completed = global_state.get("total_completed_count", 0)
        else:
            total = len(state.node_states)
            completed = _count_by_status(state, {"COMPLETED", "MASTERED"})
        if total == 0:
            return False, "no nodes in graph"
        pct = int(completed / total * 100)
        ok = pct >= minimum
        return ok, (
            f"completion {pct}% (need {minimum}%)"
            if ok
            else f"need {minimum}% completion, have {pct}%"
        )

    if rule_type == "score_gte":
        node_id = rule.get("node_id", "")
        # Use global all_node_scores if available for cross-graph lookup
        all_scores = (global_state or {}).get("all_node_scores", {})
        # Empty node_id means "any node qualifies"
        if node_id == "":
            if all_scores:
                for nid, score in all_scores.items():
                    if score >= minimum:
                        return True, f"globally: score {score} >= {minimum} (node {nid})"
            for ns in state.node_states.values():
                if ns.score >= minimum:
                    return True, f"score {ns.score} >= {minimum} (node {ns.node_id})"
            return False, f"no node has score >= {minimum}"
        # Check global scores first for specific node
        if node_id in all_scores and all_scores[node_id] >= minimum:
            return True, f"globally: score {all_scores[node_id]} >= {minimum}"
        ns = state.node_states.get(node_id)
        if ns is None:
            return False, f"node '{node_id}' not found in current graph"
        ok = ns.score >= minimum
        return ok, (
            f"score {ns.score} >= {minimum}"
            if ok
            else f"need score >= {minimum}, have {ns.score}"
        )

    if rule_type == "xp_gte":
        xp = (global_state or {}).get("total_xp", state.total_xp)
        ok = xp >= minimum
        return ok, (
            f"XP {xp} >= {minimum}"
            if ok
            else f"need {minimum} XP, have {xp}"
        )

    if rule_type == "mastered_count":
        if global_state:
            mastered = global_state.get("total_mastered_count", 0)
        else:
            mastered = _count_by_status(state, {"MASTERED"})
        ok = mastered >= minimum
        return ok, (
            f"mastered {mastered}/{minimum}"
            if ok
            else f"need {minimum} mastered, have {mastered}"
        )

    if rule_type == "streak":
        all_history = _get_all_history(state, global_state)
        days = _count_streak_days_from_entries(all_history)
        ok = days >= minimum
        return ok, (
            f"streak {days}/{minimum} days"
            if ok
            else f"need {minimum} day streak, have {days}"
        )

    if rule_type == "night_owl":
        all_history = _get_all_history(state, global_state)
        ok = _has_night_activity_from_entries(all_history)
        return ok, ("night activity detected" if ok else "no night activity detected")

    if rule_type == "first_graph":
        ok = len(state.node_states) > 0
        return ok, ("graph loaded" if ok else "no graph loaded")

    if rule_type == "undo_used":
        ok = len(state.undo_stack) > 0
        return ok, ("undo used" if ok else "undo not used")

    if rule_type == "custom_score":
        for ns in state.node_states.values():
            if ns.custom_dims:
                return True, "custom dimensions present"
        return False, "no custom dimensions"

    if rule_type == "onboarded":
        return True, "onboarding complete"

    if rule_type == "multi_graph":
        count = (global_state or {}).get("graphs_completed", 0)
        ok = count >= minimum
        return ok, (
            f"completed {count}/{minimum} graphs"
            if ok
            else f"need {minimum} completed graphs, have {count}"
        )

    if rule_type == "explorer":
        target = rule.get("count", 3)
        loaded = (global_state or {}).get("graphs_loaded", 0)
        ok = loaded >= target
        return ok, (
            f"explored {loaded}/{target} graphs"
            if ok
            else f"need {target} graphs loaded, have {loaded}"
        )

    if rule_type == "speed_run":
        all_history = _get_all_history(state, global_state)
        return _check_speed_run_from_entries(all_history, rule.get("hours", 24))

    if rule_type == "daily_completed":
        minimum = rule.get("min", 3)
        hours = rule.get("hours", 24)
        all_history = _get_all_history(state, global_state)
        ok, reason = _check_daily_completed(all_history, minimum, hours)
        return ok, reason

    if rule_type == "review_count":
        if global_state:
            count = global_state.get("total_review_count", 0)
        else:
            count = _count_reviews(state)
        ok = count >= minimum
        return ok, (
            f"reviewed {count}/{minimum} times"
            if ok
            else f"need {minimum} reviews, have {count}"
        )

    return False, f"unknown rule type: {rule_type}"


def _count_streak_days(state: UserState) -> int:
    from datetime import datetime, timedelta
    dates = set()
    for entry in state.history:
        try:
            dt = datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00"))
            dates.add(dt.date())
        except:
            pass
    if not dates:
        return 0
    sorted_dates = sorted(dates)
    max_streak = 1
    current_streak = 1
    for i in range(1, len(sorted_dates)):
        if sorted_dates[i] - sorted_dates[i-1] == timedelta(days=1):
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1
    return max_streak


def _has_night_activity(state: UserState) -> bool:
    from datetime import datetime
    for entry in state.history:
        try:
            dt = datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00"))
            hour = dt.hour
            if hour >= 22 or hour < 6:
                return True
        except:
            pass
    return False


def _count_by_status(state: UserState, statuses: set[str]) -> int:
    """Count nodes whose status is in *statuses*."""
    return sum(
        1 for ns in state.node_states.values() if ns.status.value in statuses
    )


def _check_speed_run(state: UserState, max_hours: int = 24) -> tuple[bool, str]:
    """Check if all completed nodes were first finished within *max_hours*.

    Scans history for the first COMPLETED/MASTERED event per node,
    then checks if the time span from earliest to latest is <= max_hours.
    Requires at least 2 completed nodes.
    """
    from datetime import datetime, timedelta
    first_completion: dict[str, datetime] = {}
    for entry in state.history:
        if entry.field == "status" and entry.new_value in ("COMPLETED", "MASTERED"):
            if entry.node_id not in first_completion:
                try:
                    dt = datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00"))
                    first_completion[entry.node_id] = dt
                except (ValueError, TypeError):
                    pass

    if len(first_completion) < 2:
        return False, f"only {len(first_completion)} completed, need >= 2 for speed run"

    times = sorted(first_completion.values())
    span_hours = (times[-1] - times[0]).total_seconds() / 3600
    ok = span_hours <= max_hours
    return ok, (
        f"speed run: {span_hours:.1f}h <= {max_hours}h ({len(first_completion)} nodes)"
        if ok
        else f"need all within {max_hours}h, span was {span_hours:.1f}h ({len(first_completion)} nodes)"
    )


def _count_reviews(state: UserState) -> int:
    """Count total review events (score add operations across all nodes)."""
    count = 0
    for entry in state.history:
        if entry.field == "score":
            try:
                old_s = int(entry.old_value)
                new_s = int(entry.new_value)
                if new_s > old_s:
                    count += 1
            except (ValueError, TypeError):
                pass
    return count


def _get_all_history(state: UserState, global_state: dict | None = None) -> list:
    """Merge current graph history with global history from global_state."""
    entries = list(state.history)
    
    if global_state:
        global_history = global_state.get("learning_history", [])
        entries.extend(global_history)
    
    return entries


def _count_streak_days_from_entries(entries: list) -> int:
    """Count consecutive days with activity from a list of history entries."""
    from datetime import datetime, timedelta
    
    dates = set()
    for entry in entries:
        try:
            timestamp = entry.timestamp if hasattr(entry, 'timestamp') else entry.get('timestamp', '')
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            dates.add(dt.date())
        except:
            pass
    
    if not dates:
        return 0
    
    sorted_dates = sorted(dates)
    max_streak = 1
    current_streak = 1
    
    for i in range(1, len(sorted_dates)):
        if sorted_dates[i] - sorted_dates[i-1] == timedelta(days=1):
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1
    
    return max_streak


def _has_night_activity_from_entries(entries: list) -> bool:
    """Check if any entry occurred during night hours (22:00-06:00)."""
    from datetime import datetime
    
    for entry in entries:
        try:
            timestamp = entry.timestamp if hasattr(entry, 'timestamp') else entry.get('timestamp', '')
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            hour = dt.hour
            if hour >= 22 or hour < 6:
                return True
        except:
            pass
    
    return False


def _check_speed_run_from_entries(entries: list, max_hours: int = 24) -> tuple[bool, str]:
    """Check if all completed nodes were first finished within max_hours."""
    from datetime import datetime, timedelta
    
    first_completion: dict[str, datetime] = {}
    for entry in entries:
        field = entry.field if hasattr(entry, 'field') else entry.get('field', '')
        new_value = entry.new_value if hasattr(entry, 'new_value') else entry.get('new_value', '')
        node_id = entry.node_id if hasattr(entry, 'node_id') else entry.get('node_id', '')
        
        if field == "status" and new_value in ("COMPLETED", "MASTERED"):
            if node_id not in first_completion:
                try:
                    timestamp = entry.timestamp if hasattr(entry, 'timestamp') else entry.get('timestamp', '')
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    first_completion[node_id] = dt
                except (ValueError, TypeError):
                    pass
    
    if len(first_completion) < 2:
        return False, f"only {len(first_completion)} completed, need >= 2 for speed run"
    
    times = sorted(first_completion.values())
    span_hours = (times[-1] - times[0]).total_seconds() / 3600
    ok = span_hours <= max_hours
    
    return ok, (
        f"speed run: {span_hours:.1f}h <= {max_hours}h ({len(first_completion)} nodes)"
        if ok
        else f"need all within {max_hours}h, span was {span_hours:.1f}h ({len(first_completion)} nodes)"
    )


def _check_daily_completed(entries: list, min_completed: int = 3, hours: int = 24) -> tuple[bool, str]:
    """Check if at least min_completed nodes were completed within any hours window."""
    from datetime import datetime, timedelta
    
    completion_timestamps = []
    for entry in entries:
        field = entry.field if hasattr(entry, 'field') else entry.get('field', '')
        new_value = entry.new_value if hasattr(entry, 'new_value') else entry.get('new_value', '')
        old_value = entry.old_value if hasattr(entry, 'old_value') else entry.get('old_value', '')
        
        if field == "score":
            try:
                new_s = int(new_value)
                old_s = int(old_value) if old_value else 0
                if new_s >= 5 and old_s < 5:
                    timestamp = entry.timestamp if hasattr(entry, 'timestamp') else entry.get('timestamp', '')
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    completion_timestamps.append(dt)
            except (ValueError, TypeError):
                pass
    
    completion_timestamps.sort()
    
    if len(completion_timestamps) < min_completed:
        return False, f"only {len(completion_timestamps)} completed, need {min_completed}"
    
    window = timedelta(hours=hours)
    for i in range(len(completion_timestamps) - min_completed + 1):
        window_end = completion_timestamps[i] + window
        count = 0
        for j in range(i, len(completion_timestamps)):
            if completion_timestamps[j] <= window_end:
                count += 1
            else:
                break
        if count >= min_completed:
            return True, f"{count} nodes completed within {hours}h window"
    
    return False, f"no {hours}h window contains {min_completed} completions"
