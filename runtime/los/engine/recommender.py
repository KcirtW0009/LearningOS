"""Recommendation Engine — suggests next learning actions.

Defined by: REC-001 (Phase 9)

Strategies:
  1. next_available — nodes unlocked and ready to learn (by difficulty)
  2. optimal_path — shortest path to a target node
  3. weak_areas — completed nodes with low scores (review suggestions)
  4. difficulty_sequence — nodes at user's appropriate difficulty level
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from los.runtime.runtime_instance import RuntimeInstance


def recommend_next_available(rt: RuntimeInstance) -> list[str]:
    """Return available nodes sorted by difficulty (beginner first)."""
    avail = rt.get_available_nodes()
    if not avail:
        return []
    difficulty_order = {"beginner": 0, "intermediate": 1, "advanced": 2}

    def _sort_key(node_id: str) -> int:
        detail = rt.get_node_detail(node_id)
        if detail is None:
            return 99
        return difficulty_order.get(str(detail.get("difficulty", "")), 99)

    return sorted(avail, key=_sort_key)


def recommend_weak_areas(rt: RuntimeInstance, threshold: int = 5) -> list[dict]:
    """Return completed nodes where score < threshold (suggest review)."""
    progress = rt.get_progress_snapshot()
    if progress.completed == 0:
        return []

    weak = []
    for ns in rt._state.node_states.values():
        if ns.is_completed and ns.score < threshold:
            detail = rt.get_node_detail(ns.node_id)
            if detail:
                weak.append({
                    "node_id": ns.node_id,
                    "title": detail.get("title", ns.node_id),
                    "score": ns.score,
                    "difficulty": detail.get("difficulty", ""),
                })
    return weak


def recommend_optimal_path(rt: RuntimeInstance, target_id: str) -> dict:
    """BFS shortest path from available nodes to *target_id*.

    Step 1: Try old BFS (available -> target). If succeeds -> return as-is.
    Step 2: If old BFS returns empty AND target exists: do REVERSE BFS
            from target, walking BACKWARDS over ALL blocking prereq edges.
    Step 3: Topologically sort the ancestor chain.
    Step 4: Split into pre_path (uncompleted) and done_nodes (completed).

    Returns a dict: { reachable, direct_path, pre_path, full_path, target }
    """
    from collections import deque

    graph = rt._graph
    if not graph.node_exists(target_id):
        return {
            "reachable": False,
            "target_finished": False,
            "target_status": None,
            "direct_path": [],
            "pre_path": [],
            "full_path": [],
            "target": target_id,
        }

    available = set(rt.get_available_nodes())
    if target_id in available:
        ns_target = rt._state.get_node_state(target_id)
        return {
            "reachable": True,
            "target_finished": False,
            "target_status": ns_target.status.value if ns_target else "AVAILABLE",
            "direct_path": [target_id],
            "pre_path": [],
            "full_path": [target_id],
            "target": target_id,
        }

    # ── Early special case: target is already completed/mastered ──
    ns_target = rt._state.get_node_state(target_id)
    if ns_target and ns_target.is_completed:
        # Build full prerequisite chain (for display as review path)
        ancestors_t: set[str] = set()
        rq_t: deque[str] = deque([target_id])
        ancestors_t.add(target_id)
        while rq_t:
            cur = rq_t.popleft()
            for s in graph.get_blocking_source_ids(cur):
                if s not in ancestors_t:
                    ancestors_t.add(s)
                    rq_t.append(s)
        # Topo-sort the ancestor subgraph
        deg_t: dict[str, int] = {n: 0 for n in ancestors_t}
        sub_t: dict[str, list[str]] = {n: [] for n in ancestors_t}
        for n in ancestors_t:
            for s in graph.get_blocking_source_ids(n):
                if s in ancestors_t:
                    sub_t[s].append(n)
                    deg_t[n] += 1
        tq: deque[str] = deque([n for n in ancestors_t if deg_t[n] == 0])
        full_path_t: list[str] = []
        while tq:
            cur = tq.popleft()
            full_path_t.append(cur)
            for nb in sub_t[cur]:
                deg_t[nb] -= 1
                if deg_t[nb] == 0:
                    tq.append(nb)
        pre_path_t = [nid for nid in full_path_t if rt._state.get_node_state(nid) is None or not rt._state.get_node_state(nid).is_completed]
        return {
            "reachable": True,
            "target_finished": True,
            "target_status": ns_target.status.value,
            "direct_path": [],
            "pre_path": pre_path_t,
            "full_path": full_path_t,
            "target": target_id,
        }

    # Step 1: Try old BFS (available -> target)
    visited: set[str] = set()
    queue: deque[list[str]] = deque()

    for node_id in available:
        queue.append([node_id])
        visited.add(node_id)

    direct_path: list[str] = []
    while queue:
        path = queue.popleft()
        current = path[-1]
        if current == target_id:
            direct_path = path
            break

        for edge in graph.get_edges_from(current):
            neighbor = edge.target
            if neighbor not in visited and not _is_blocked_by_prereq(rt, neighbor, visited):
                visited.add(neighbor)
                queue.append(path + [neighbor])

    if direct_path:
        ns_final = rt._state.get_node_state(target_id)
        return {
            "reachable": True,
            "target_finished": False,
            "target_status": ns_final.status.value if ns_final else None,
            "direct_path": direct_path,
            "pre_path": [],
            "full_path": direct_path,
            "target": target_id,
        }

    # Step 2: Reverse BFS from target over ALL blocking prerequisite edges
    ancestors: set[str] = set()
    reverse_queue: deque[str] = deque([target_id])
    ancestors.add(target_id)

    while reverse_queue:
        current = reverse_queue.popleft()
        blocking_sources = graph.get_blocking_source_ids(current)
        for src in blocking_sources:
            if src not in ancestors:
                ancestors.add(src)
                reverse_queue.append(src)

    # Step 3: Topologically sort the ancestor chain
    # Build subgraph of ancestors only
    in_degree: dict[str, int] = {n: 0 for n in ancestors}
    subgraph_edges: dict[str, list[str]] = {n: [] for n in ancestors}

    for n in ancestors:
        for src in graph.get_blocking_source_ids(n):
            if src in ancestors:
                subgraph_edges[src].append(n)
                in_degree[n] += 1

    topo_queue: deque[str] = deque([n for n in ancestors if in_degree[n] == 0])
    full_path: list[str] = []
    while topo_queue:
        current = topo_queue.popleft()
        full_path.append(current)
        for neighbor in subgraph_edges[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                topo_queue.append(neighbor)

    # Step 4: Split into pre_path (uncompleted) and done_nodes (completed)
    pre_path: list[str] = []
    for nid in full_path:
        ns = rt._state.get_node_state(nid)
        if ns is None or not ns.is_completed:
            pre_path.append(nid)

    ns_target_final = rt._state.get_node_state(target_id)
    return {
        "reachable": False,
        "target_finished": False,
        "target_status": ns_target_final.status.value if ns_target_final else None,
        "direct_path": [],
        "pre_path": pre_path,
        "full_path": full_path,
        "target": target_id,
    }


def _is_blocked_by_prereq(rt: RuntimeInstance, node_id: str, visited: set[str]) -> bool:
    """Check if *node_id* has unmet prerequisites outside the *visited* set."""
    graph = rt._graph
    blocking = graph.get_blocking_source_ids(node_id)
    for src in blocking:
        ns = rt._state.get_node_state(src)
        if ns is None or not ns.is_completed:
            return True
    return False


def recommend_difficulty_sequence(
    rt: RuntimeInstance,
    target_difficulty: str | None = None,
) -> list[str]:
    """Recommend nodes filtered by difficulty.

    If *target_difficulty* is None, recommends the most appropriate
    difficulty level based on completed node difficulties.
    Defaults to 'beginner' if no pattern detected.
    """
    progress = rt.get_progress_snapshot()
    if progress.completed == 0:
        target_difficulty = "beginner"

    if target_difficulty is None:
        # Detect user's difficulty sweet spot
        difficulty_counts: dict[str, int] = {}
        for ns in rt._state.node_states.values():
            if ns.is_completed:
                detail = rt.get_node_detail(ns.node_id)
                if detail:
                    d = str(detail.get("difficulty", ""))
                    difficulty_counts[d] = difficulty_counts.get(d, 0) + 1
        if difficulty_counts:
            target_difficulty = max(difficulty_counts, key=difficulty_counts.get)
        else:
            target_difficulty = "beginner"

    all_nodes = rt._graph.get_all_nodes()
    result = []
    for node in all_nodes:
        if node.difficulty == target_difficulty:
            ns = rt._state.get_node_state(node.id)
            if ns is None or not ns.is_completed:
                result.append(node.id)

    return result
