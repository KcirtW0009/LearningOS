"""CLI adapter — argparse-based command interface.

Defined by:
  - LOS-0402 Command Interface
  - LOS-0500 Phase 8 CLI Interface
  - Phase 8 Design Review (approved)
  - Phase 2 RuntimeInstance Migration

Responsibility:
  - argument parsing
  - command dispatch
  - delegating to RuntimeInstance (thin presentation layer)
  - formatting output

MUST NOT:
  - implement availability calculation
  - implement prerequisite logic
  - implement state transition rules
  - implement persistence serialization
"""

from __future__ import annotations

import argparse
import sys
import uuid
from typing import Callable

import yaml

from los.exceptions import LOSError
from los.runtime.runtime_instance import RuntimeInstance
from los.session import Session, get_binding


# ── Session state (CLI process lifetime only) ────────────────────
_binding = get_binding()


# ── Public: build parser ──────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level argument parser with subcommands."""
    p = argparse.ArgumentParser(
        prog="los",
        description="Learning OS Runtime — a local-first, graph-driven learning runtime",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # ── graph ─────────────────────────────────────────────────────
    gp = sub.add_parser("graph", help="Graph Package operations")
    gsub = gp.add_subparsers(dest="graph_command", required=True)

    gl = gsub.add_parser("load", help="Load a Graph Package")
    gl.add_argument("path", help="Path to Graph Package directory")

    gsub.add_parser("info", help="Show current Graph information")

    # ── node ──────────────────────────────────────────────────────
    np = sub.add_parser("node", help="Node operations")
    nsub = np.add_subparsers(dest="node_command", required=True)

    nsub.add_parser("list", help="List available Nodes")

    ni = nsub.add_parser("info", help="Show Node details")
    ni.add_argument("node_id", help="Node identifier")

    nc = nsub.add_parser("complete", help="Mark a Node as completed")
    nc.add_argument("node_id", help="Node identifier")
    nc.add_argument("--score", type=int, default=10, help="Completion score (default: 10)")
    nc.add_argument("--evidence", nargs="*", default=None, help="Evidence references")

    nr = nsub.add_parser("reset", help="Hard-reset a Node to NOT_STARTED")
    nr.add_argument("node_id", help="Node identifier")

    nsub.add_parser("undo", help="Step-undo: reverse the most recent node action")

    ns = nsub.add_parser("score", help="Add a self-assessment score event")
    ns.add_argument("node_id", help="Node identifier")
    ns.add_argument("score_delta", type=int, help="Score points to add (positive integer)")
    ns.add_argument("--description", "-d", default="", help="Description of the learning activity")

    # Undo stack
    nsub.add_parser("undo-stack", help="Show the undo stack (time-based timeline)")

    # ── status ────────────────────────────────────────────────────
    sub.add_parser("status", help="Show learning progress")

    # ── export ────────────────────────────────────────────────────
    ep = sub.add_parser("export", help="Export operations")
    esub = ep.add_subparsers(dest="export_command", required=True)
    esub.add_parser("prompt", help="Export a standardized prompt for external AI")
    esub.add_parser("progress", help="Export current learning progress as JSON")

    # ── import ────────────────────────────────────────────────────
    ip = sub.add_parser("import", help="Import operations")
    isub = ip.add_subparsers(dest="import_command", required=True)
    imp = isub.add_parser("progress", help="Import learning progress from JSON")
    imp.add_argument("file", help="Path to the progress JSON file")

    # ── xp (Phase 7) ──────────────────────────────────────────────
    sub.add_parser("xp", help="Show XP and level")

    # ── achievements (Phase 7) ────────────────────────────────────
    sub.add_parser("achievements", help="Show achievements")

    return p


# ── State reload (across process invocations) ─────────────────────


def _ensure_loaded() -> str | None:
    """Auto-load graph and state from disk if session is empty.

    Returns an error string on failure, or None on success.
    Called by every handler that requires state.
    """
    if _binding.current_runtime is not None:
        return None  # already loaded this process

    runtime = RuntimeInstance.resume()
    if runtime is None:
        return "No graph loaded. Run: los graph load <package>"

    _binding.bind(Session(session_id=uuid.uuid4().hex[:12], user_id="default"), runtime)
    return None


# ── Command handlers ──────────────────────────────────────────────


def handle_graph_load(args: argparse.Namespace) -> str:
    """Load a Graph Package via RuntimeInstance."""

    try:
        runtime = RuntimeInstance.load(args.path)
    except LOSError as e:
        return _error(str(e))
    except yaml.YAMLError as e:
        return _error(f"Invalid YAML: {e}")

    _binding.bind(Session(session_id=uuid.uuid4().hex[:12], user_id="default"), runtime)
    info = _binding.current_runtime.get_graph_info()
    return (
        f"Loaded: {info['package_name']} v{info['package_version']}\n"
        f"  {info['node_count']} nodes, {info['edge_count']} edges"
    )


def handle_graph_info(args: argparse.Namespace) -> str:
    """Display current Graph metadata."""
    err = _ensure_loaded()
    if err:
        return _error(err)

    info = _binding.current_runtime.get_graph_info()
    return (
        f"Package: {info['package_id']}\n"
        f"Name:    {info['package_name']}\n"
        f"Version: {info['package_version']}\n"
        f"Author:  {info['author']}\n"
        f"Nodes:   {info['node_count']}\n"
        f"Edges:   {info['edge_count']}"
    )


def handle_node_list(args: argparse.Namespace) -> str:
    """List AVAILABLE nodes."""
    err = _ensure_loaded()
    if err:
        return _error(err)

    available = _binding.current_runtime.get_available_nodes()
    if not available:
        return "No nodes available."

    lines = ["Available:"]
    for i, nid in enumerate(available, 1):
        detail = _binding.current_runtime.get_node_detail(nid)
        if detail is None:
            continue
        suffix = ""
        if detail["difficulty"] != "(none)":
            suffix = f" [{detail['difficulty']}]"
        lines.append(f"  {i}. {detail['title']}{suffix}")
    return "\n".join(lines)


def handle_node_info(args: argparse.Namespace) -> str:
    """Display detailed information about a single Node."""
    err = _ensure_loaded()
    if err:
        return _error(err)

    detail = _binding.current_runtime.get_node_detail(args.node_id)
    if detail is None:
        return _error(f"Unknown node: '{args.node_id}'")

    return (
        f"ID:          {detail['id']}\n"
        f"Title:       {detail['title']}\n"
        f"Description: {detail['description']}\n"
        f"Type:        {detail['type']}\n"
        f"Difficulty:  {detail['difficulty']}\n"
        f"Status:      {detail['status']}\n"
        f"Score:       {detail['score']}\n"
        f"Evidence:    {detail['evidence']}\n"
        + _format_resources(detail.get("resources", []))
    )


def handle_node_complete(args: argparse.Namespace) -> str:
    """Validate eligibility and complete a Node."""
    err = _ensure_loaded()
    if err:
        return _error(err)

    score = getattr(args, "score", 10) or 10
    evidence = getattr(args, "evidence", None)

    try:
        result = _binding.current_runtime.complete_node(
            args.node_id, score=score, evidence=evidence
        )
    except ValueError as e:
        return _error(str(e))

    return result


def handle_node_reset(args: argparse.Namespace) -> str:
    """Hard-reset a Node back to NOT_STARTED."""
    err = _ensure_loaded()
    if err:
        return _error(err)

    try:
        result = _binding.current_runtime.reset_node(args.node_id)
    except ValueError as e:
        return _error(str(e))

    return result


def handle_node_undo(_args: argparse.Namespace) -> str:
    """Step-undo: reverse the most recent node mutation."""
    err = _ensure_loaded()
    if err:
        return _error(err)

    try:
        result = _binding.current_runtime.undo_last_action()
    except ValueError as e:
        return _error(str(e))

    return result


def handle_undo_stack(_args: argparse.Namespace) -> str:
    """Show the undo stack with timestamps."""
    err = _ensure_loaded()
    if err:
        return _error(err)

    runtime = _binding.current_runtime
    stack = list(runtime._state.undo_stack)

    if not stack:
        return "Undo stack is empty."

    lines = [f"Undo Stack ({len(stack)} entries, unlimited):"]
    for i, e in enumerate(reversed(stack)):
        node_title = runtime.get_node_detail(e.node_id)
        title = node_title["title"] if node_title else e.node_id
        lines.append(
            f"  #{i}: {e.timestamp} | {e.action} | {title} "
            f"(was {e.previous_status})"
        )
    return "\n".join(lines)


def handle_node_score(args: argparse.Namespace) -> str:
    """Add a self-assessment score event to a Node."""
    err = _ensure_loaded()
    if err:
        return _error(err)

    try:
        result = _binding.current_runtime.add_score_event(
            args.node_id,
            score_delta=args.score_delta,
            description=args.description,
        )
    except ValueError as e:
        return _error(str(e))

    return result


def handle_status(args: argparse.Namespace) -> str:
    """Display learning progress summary."""
    err = _ensure_loaded()
    if err:
        return _error(err)

    progress = _binding.current_runtime.get_progress()
    info = _binding.current_runtime.get_graph_info()

    return (
        f"Graph:    {info['package_name']} v{info['package_version']}\n"
        f"Progress: {progress['completed']}/{progress['total']} ({progress['percentage']}%)\n"
        f"  Mastered:  {progress['mastered']}\n"
        f"Available: {progress['available']}\n"
        f"Locked:    {progress['locked']}"
    )


# ── XP handler (Phase 7) ────────────────────────────────────────────


def handle_xp(_args: argparse.Namespace) -> str:
    """Display XP and level."""
    from los.engine.xp import compute_total_xp, get_level, xp_to_next_level

    err = _ensure_loaded()
    if err:
        return _error(err)

    runtime = _binding.current_runtime
    state = runtime._state
    total = state.total_xp or compute_total_xp(state)
    level = get_level(total)
    next_lvl = xp_to_next_level(total)

    return (
        f"Total XP:   {total}\n"
        f"Level:      {level}\n"
        f"Next level: {next_lvl} XP to go"
    )


# ── Achievements handler (Phase 7) ──────────────────────────────────


def handle_achievements(_args: argparse.Namespace) -> str:
    """Display achievements."""
    from los.engine.achievements import check_achievements

    err = _ensure_loaded()
    if err:
        return _error(err)

    runtime = _binding.current_runtime
    results = check_achievements(runtime._state)

    earned = [ach for ach, ok in results if ok]
    locked = [ach for ach, ok in results if not ok]

    lines = ["Achievements:"]
    for ach in earned:
        lines.append(f"  [*] {ach.name} -- {ach.description}")
    for ach in locked:
        lines.append(f"  [ ] {ach.name} -- {ach.description}")

    return "\n".join(lines)


def handle_export_prompt(_args: argparse.Namespace) -> str:
    """Export a standardized prompt for external AI."""
    import json, urllib.request

    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/export/prompt") as resp:
            data = json.loads(resp.read().decode())
            return data.get("prompt", "No prompt generated")
    except Exception as e:
        return _error(f"Failed to connect to API: {e}")


def handle_export_progress(_args: argparse.Namespace) -> str:
    """Export current learning progress as JSON."""
    import json, os

    err = _ensure_loaded()
    if err:
        return _error(err)

    rt = _binding.current_runtime
    data = rt.export_progress()

    out_path = "data/export-progress.json"
    os.makedirs("data", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return f"Progress exported to {out_path}"


def handle_import_progress(args: argparse.Namespace) -> str:
    """Import learning progress from a JSON file."""
    import json, os

    file_path = args.file
    if not os.path.isfile(file_path):
        return _error(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    err = _ensure_loaded()
    if err:
        return _error(err)

    rt = _binding.current_runtime
    try:
        msg = rt.import_progress(data)
    except ValueError as e:
        return _error(str(e))

    progress = rt.get_progress()
    return (
        f"{msg}\n"
        f"  Mastered: {progress['mastered']} | "
        f"Percentage: {progress['percentage']}%"
    )


# ── Dispatch table ─────────────────────────────────────────────────

_DISPATCH: dict[str, Callable[[argparse.Namespace], str]] = {
    "graph.load":    handle_graph_load,
    "graph.info":    handle_graph_info,
    "node.list":     handle_node_list,
    "node.info":     handle_node_info,
    "node.complete": handle_node_complete,
    "node.reset":    handle_node_reset,
    "node.undo":     handle_node_undo,
    "node.undo-stack": handle_undo_stack,
    "node.score":    handle_node_score,
    "status":        handle_status,
    "xp":            handle_xp,
    "achievements":  handle_achievements,
    "export.prompt":   handle_export_prompt,
    "export.progress": handle_export_progress,
    "import.progress": handle_import_progress,
}


def dispatch(args: argparse.Namespace) -> str:
    """Route parsed args to the correct handler."""
    key = args.command
    if key == "graph":
        key = f"graph.{args.graph_command}"
    elif key == "node":
        key = f"node.{args.node_command}"
    elif key == "export":
        key = f"export.{args.export_command}"
    elif key == "import":
        key = f"import.{args.import_command}"

    handler = _DISPATCH.get(key)
    if handler is None:
        return _error(f"Unknown command: {key}")
    return handler(args)


# ── Helpers ────────────────────────────────────────────────────────

def _error(msg: str) -> str:
    return f"Error: {msg}"


def _format_resources(resources: list[dict]) -> str:
    """Format a list of Resource dicts for CLI display."""
    if not resources:
        return ""
    lines = ["Resources:"]
    for i, r in enumerate(resources):
        label = f" [{r['label']}]" if r.get("label") else ""
        lines.append(f"  {i + 1}. {r['type']}:{label} {r['uri']}")
    return "\n".join(lines)
