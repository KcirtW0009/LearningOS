"""REST API server — FastAPI wrapper over RuntimeInstance.

Phase 8 — Interface Layer

Endpoints:
  POST   /graph/load              — Load a graph package
  GET    /graph/info              — Get current graph info
  GET    /nodes                   — List available nodes
  GET    /nodes/{node_id}         — Get node detail
  POST   /nodes/{node_id}/complete — Complete a node
  GET    /status                  — Get progress summary
  GET    /xp                      — Get XP and level
  GET    /achievements            — Get achievement status
  GET    /health                  — Health check
"""

from __future__ import annotations

import json
import os
import pathlib
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from los.runtime.runtime_instance import RuntimeInstance
from los.session import Session, get_binding
from los.graph.models import VALID_RELATIONS
from los.common import utc_now_iso as _utc_now_iso

# ── App ──────────────────────────────────────────────────────────────

app = FastAPI(title="LearningOS Runtime API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

_binding = get_binding()


# ── Models ────────────────────────────────────────────────────────────


class CompleteRequest(BaseModel):
    score: int = 10
    evidence: list[str] | None = None

    @field_validator("score")
    @classmethod
    def score_must_be_valid(cls, v: int) -> int:
        if v < 0:
            raise ValueError("score must be >= 0")
        if v > 100:
            raise ValueError("score must be <= 100")
        return v


class CustomDimRequest(BaseModel):
    dim_name: str
    score: int

    @field_validator("dim_name")
    @classmethod
    def dim_name_must_be_valid(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("dim_name must not be empty")
        if len(v) > 32:
            raise ValueError("dim_name must be <= 32 characters")
        return v

    @field_validator("score")
    @classmethod
    def score_must_be_valid(cls, v: int) -> int:
        if not isinstance(v, int):
            raise ValueError("score must be an integer")
        if v < 0:
            raise ValueError("score must be >= 0")
        if v > 100:
            raise ValueError("score must be <= 100")
        return v


class LoadRequest(BaseModel):
    path: str


# ── Project root resolution ───────────────────────────────────────────
# server.py lives at <project>/runtime/los/api/server.py
_PROJECT_ROOT = os.environ.get(
    "LEARNINGOS_PROJECT_ROOT",
    os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
)

# ── Data directory — respects LEARNINGOS_DATA_DIR for packaged mode ───
_DATA_DIR = os.environ.get("LEARNINGOS_DATA_DIR", os.path.join(_PROJECT_ROOT, "data"))

# ── Security: path traversal guard ────────────────────────────────────

_SAFE_PREFIX = os.environ.get(
    "LEARNINGOS_GRAPHS_DIR",
    os.path.join(_PROJECT_ROOT, "graphs")
)

def _validate_graph_path(path: str) -> str:
    """Validate that *path* is within the allowed graphs/ directory.

    Returns the absolute path resolved from the graphs directory.
    """
    normalized = os.path.normpath(path)
    if os.path.isabs(normalized):
        raise HTTPException(
            status_code=400,
            detail="Graph path must be relative, not absolute",
        )
    if ".." in normalized.split(os.sep):
        raise HTTPException(
            status_code=400,
            detail="Graph path must not contain '..' (path traversal)",
        )
    
    if normalized.startswith("graphs/") or normalized.startswith("graphs\\"):
        normalized = normalized[7:]
    
    resolved = os.path.normpath(os.path.join(_SAFE_PREFIX, normalized))
    if not resolved.startswith(_SAFE_PREFIX + os.sep) and resolved != _SAFE_PREFIX:
        raise HTTPException(
            status_code=400,
            detail=f"Graph path must be under '{_SAFE_PREFIX}/' directory",
        )
    return resolved


# ── Structured error handler ──────────────────────────────────────────

@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "suggestion": _suggestion_for_status(exc.status_code),
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc),
                "suggestion": "Please check the server logs or try again later",
            }
        },
    )


@app.exception_handler(ValueError)
async def validation_exception_handler(_request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(exc),
                "suggestion": "Check the request parameters and try again",
            }
        },
    )


def _suggestion_for_status(code: int) -> str:
    suggestions = {
        400: "Verify your request parameters and try again",
        404: "The requested resource was not found — check the ID or path",
        422: "The request data failed validation — check the field values",
        500: "An unexpected server error occurred — try again or check logs",
    }
    return suggestions.get(code, "Please try again or contact support")


# ── Dependency ────────────────────────────────────────────────────────


def _get_runtime() -> RuntimeInstance:
    """Return the currently bound RuntimeInstance, or raise 400."""
    rt = _binding.current_runtime
    if rt is None:
        raise HTTPException(
            status_code=400,
            detail="No graph loaded. Use POST /graph/load first",
        )
    return rt


# ── Graph ─────────────────────────────────────────────────────────────


@app.post("/graph/load")
def api_graph_load(body: LoadRequest) -> dict[str, Any]:
    """Load a Graph Package. Creates a new Session and binds it."""
    safe_path = _validate_graph_path(body.path)
    try:
        runtime = RuntimeInstance.load(safe_path)
        session = Session(session_id=uuid.uuid4().hex[:12], user_id="default")
        _binding.bind(session, runtime)
        info = runtime.get_graph_info()
        return {
            "status": "loaded",
            "package_name": info["package_name"],
            "package_version": info["package_version"],
            "node_count": info["node_count"],
            "edge_count": info["edge_count"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/graph/info")
def api_graph_info() -> dict[str, Any]:
    rt = _get_runtime()
    return rt.get_graph_info()


@app.get("/graph/edges")
def api_graph_edges() -> list[dict[str, Any]]:
    """Return all edges for visualization."""
    rt = _get_runtime()
    edges = []
    for edge in rt._graph.get_all_edges():
        edges.append({
            "from": edge.source,
            "to": edge.target,
            "relation": edge.relation,
        })
    return edges


# ── Nodes ──────────────────────────────────────────────────────────────


@app.get("/nodes")
def api_node_list() -> list[str]:
    rt = _get_runtime()
    return rt.get_available_nodes()


@app.get("/nodes/all")
def api_all_nodes() -> list[dict[str, Any]]:
    """Return all nodes with status info."""
    rt = _get_runtime()
    all_ids = rt.get_node_ids()
    result = []
    for nid in all_ids:
        detail = rt.get_node_detail(nid)
        if detail:
            result.append(detail)
    return result


@app.get("/nodes/{node_id}")
def api_node_detail(node_id: str) -> dict[str, Any]:
    rt = _get_runtime()
    detail = rt.get_node_detail(node_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Unknown node: '{node_id}'")
    return detail


@app.post("/nodes/{node_id}/complete")
def api_node_complete(
    node_id: str, body: CompleteRequest = CompleteRequest()
) -> dict[str, Any]:
    rt = _get_runtime()
    try:
        msg = rt.complete_node(node_id, score=body.score, evidence=body.evidence)
        return {"status": "ok", "message": msg}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/nodes/{node_id}/reset")
def api_node_reset(node_id: str) -> dict[str, Any]:
    """Hard-reset a node back to NOT_STARTED."""
    rt = _get_runtime()
    try:
        msg = rt.reset_node(node_id)
        return {"status": "ok", "message": msg}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/undo")
def api_undo() -> dict[str, Any]:
    """Step-undo: reverse the most recent node mutation."""
    rt = _get_runtime()
    try:
        msg = rt.undo_last_action()
        return {"status": "ok", "message": msg}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/undo/stack")
def api_undo_stack() -> dict[str, Any]:
    """Return the current undo stack size and recent entries."""
    rt = _get_runtime()
    stack = list(rt._state.undo_stack)
    return {
        "count": len(stack),
        "unlimited": True,
        "entries": [
            {
                "index": len(stack) - 1 - i,
                "node_id": e.node_id,
                "action": e.action,
                "previous_status": e.previous_status,
                "timestamp": e.timestamp,
            }
            for i, e in enumerate(reversed(stack))
        ],
    }


@app.post("/undo/multi")
def api_undo_multi(count: int = 1) -> dict[str, Any]:
    """Undo multiple steps at once (infinite undo support)."""
    rt = _get_runtime()
    try:
        results = rt.undo_multiple(count)
        return {
            "status": "ok",
            "undone_count": len(results),
            "entries": [
                {
                    "node_id": r.node_id,
                    "action": r.action,
                    "previous_status": r.previous_status,
                }
                for r in results
            ],
        }
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/undo/preview")
def api_undo_preview() -> dict[str, Any]:
    """Preview the impact of the next undo operation.

    Shows which dependent nodes would be affected if the user undoes
    the most recent action.  Used by the frontend to display a
    safety confirmation dialog before executing undo.
    """
    rt = _get_runtime()
    return rt.preview_undo_impact()


@app.post("/undo/cascade")
def api_undo_cascade(cascade: bool = False) -> dict[str, Any]:
    """Undo with optional cascade reset of affected dependent nodes.

    If cascade=true, also resets any COMPLETED/MASTERED nodes that
    depend on the undone node via blocking edges.

    The frontend should call GET /undo/preview first to show the user
    what will be affected, then call this endpoint with the user's choice.
    """
    rt = _get_runtime()
    try:
        summary = rt.undo_with_cascade(cascade=cascade)
        return {"status": "ok", **summary}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ── Status ─────────────────────────────────────────────────────────────


@app.get("/status")
def api_status() -> dict[str, Any]:
    rt = _get_runtime()
    progress = rt.get_progress()
    info = rt.get_graph_info()
    return {
        "package_name": info["package_name"],
        "package_version": info["package_version"],
        **progress,
    }


# ── XP / Achievements ─────────────────────────────────────────────────


def _compute_global_state() -> dict[str, Any]:
    """Compute cross-graph aggregates from GlobalUserState and graph files.

    Returns:
        {"graphs_loaded": int, "graphs_completed": int, "total_xp": int,
         "total_completed_count": int, "total_nodes": int,
         "total_mastered_count": int, "total_review_count": int,
         "all_node_scores": dict[str,int], "graph_ids": list[str]}
    """
    from los.storage.adapter import load_global_state

    gus = load_global_state()
    data_dir = _DATA_DIR
    empty = {
        "graphs_loaded": 0,
        "graphs_completed": 0,
        "total_xp": gus.total_xp,
        "total_completed_count": 0,
        "total_nodes": 0,
        "total_mastered_count": 0,
        "total_review_count": 0,
        "all_node_scores": {},
        "graph_ids": [],
    }
    if not os.path.isdir(data_dir):
        return empty

    graph_ids = []
    graphs_completed = 0
    total_completed_count = 0
    total_nodes = 0
    total_mastered_count = 0
    total_review_count = 0
    all_node_scores: dict[str, int] = {}

    for fpath in pathlib.Path(data_dir).glob("user-state-*.json"):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        gid = data.get("graph_id", "")
        if not gid:
            continue
        graph_ids.append(gid)

        node_states = data.get("node_states", {})
        if node_states:
            graph_node_count = len(node_states)
            total_nodes += graph_node_count
            completed = 0
            mastered = 0
            for nid, ns in node_states.items():
                status = ns.get("status", "")
                score = ns.get("score", 0)
                if status in ("COMPLETED", "MASTERED"):
                    completed += 1
                if status == "MASTERED":
                    mastered += 1
                if score > all_node_scores.get(nid, 0):
                    all_node_scores[nid] = score
            total_completed_count += completed
            total_mastered_count += mastered
            if graph_node_count > 0 and completed >= graph_node_count:
                graphs_completed += 1

        history = data.get("history", [])
        for entry in history:
            if entry.get("field") == "score":
                try:
                    old_s = int(entry.get("old_value", 0))
                    new_s = int(entry.get("new_value", 0))
                    if new_s > old_s:
                        total_review_count += 1
                except (ValueError, TypeError):
                    pass

    learning_history = []
    for h in gus.learning_history:
        learning_history.append({
            "node_id": h.node_id,
            "field": h.field,
            "old_value": h.old_value,
            "new_value": h.new_value,
            "timestamp": h.timestamp,
        })

    return {
        "graphs_loaded": len(graph_ids),
        "graphs_completed": graphs_completed,
        "total_xp": gus.total_xp,
        "total_completed_count": total_completed_count,
        "total_nodes": total_nodes,
        "total_mastered_count": total_mastered_count,
        "total_review_count": total_review_count,
        "all_node_scores": all_node_scores,
        "graph_ids": graph_ids,
        "unlocked_achievements": gus.unlocked_achievements,
        "learning_history": learning_history,
    }


@app.get("/xp")
def api_xp() -> dict[str, Any]:
    from los.engine.xp import compute_total_xp, get_level, xp_to_next_level

    rt = _get_runtime()
    state = rt._state
    local_xp = state.total_xp or compute_total_xp(state)
    global_xp = rt._global_state.total_xp
    global_level = get_level(global_xp)
    return {
        "total_xp": local_xp,
        "global_xp": global_xp,
        "level": global_level,
        "global_level": global_level,
        "xp_to_next_level": xp_to_next_level(global_xp),
    }


@app.get("/achievements")
def api_achievements() -> dict[str, list[dict[str, Any]]]:
    from los.engine.achievements import check_achievements

    rt = _get_runtime()
    global_state = _compute_global_state()
    results = check_achievements(rt._state, global_state=global_state)
    earned = [
        {"id": a.id, "name": a.name, "description": a.description, "icon": a.icon, "priority": a.priority}
        for a, ok in results
        if ok
    ]
    locked = [
        {"id": a.id, "name": a.name, "description": a.description, "icon": a.icon, "priority": a.priority}
        for a, ok in results
        if not ok
    ]
    return {"earned": earned, "locked": locked}


# ── Health ─────────────────────────────────────────────────────────────


@app.get("/health")
def api_health() -> dict[str, str]:
    return {"status": "ok"}


# ── Graph Package Catalog ─────────────────────────────────────────────


@app.get("/graphs/packages")
def api_graphs_packages() -> dict[str, Any]:
    """List all graph packages currently present in the graphs/ directory.

    Scans every immediate subdirectory of _SAFE_PREFIX, reads its
    manifest.yaml, and returns a sorted package catalog.  Used by the
    frontend dropdown so newly-saved graphs appear without a restart or
    code change.

    Directories without manifest.yaml or with an unreadable one are
    skipped (no crash — the operator can inspect the filesystem directly
    via standard tooling).
    """
    import yaml as _yaml

    packages: list[dict[str, Any]] = []
    if not os.path.isdir(_SAFE_PREFIX):
        return {"count": 0, "packages": packages}

    for entry in sorted(os.listdir(_SAFE_PREFIX)):
        pkg_dir = os.path.join(_SAFE_PREFIX, entry)
        if not os.path.isdir(pkg_dir):
            continue
        manifest_path = os.path.join(pkg_dir, "manifest.yaml")
        if not os.path.isfile(manifest_path):
            continue
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                mf = _yaml.safe_load(f) or {}
        except (_yaml.YAMLError, OSError):
            continue
        if not isinstance(mf, dict):
            continue

        pid = str(mf.get("package_id", entry)).strip() or entry
        name = str(mf.get("name", pid)).strip() or pid
        version = str(mf.get("version", "1.0.0")).strip() or "1.0.0"
        author = str(mf.get("author", "")).strip()
        packages.append({
            "id": pid,
            "name": name,
            "version": version,
            "author": author,
            "path": f"graphs/{entry}/",
            "node_count": None,  # Populated lazily if graph.yaml is readable
            "edge_count": None,
        })
        # Also try to read graph.yaml for node/edge counts (non-fatal)
        graph_path = os.path.join(pkg_dir, "graph.yaml")
        if os.path.isfile(graph_path):
            try:
                with open(graph_path, "r", encoding="utf-8") as f:
                    gr = _yaml.safe_load(f) or {}
                if isinstance(gr, dict):
                    nn = gr.get("nodes", [])
                    ne = gr.get("edges", [])
                    packages[-1]["node_count"] = len(nn) if isinstance(nn, list) else None
                    packages[-1]["edge_count"] = len(ne) if isinstance(ne, list) else None
            except (_yaml.YAMLError, OSError):
                pass

    packages.sort(key=lambda p: (p["name"].lower(), p["id"]))
    return {"count": len(packages), "packages": packages}


# ── Graph Generator (External AI Interface) ───────────────────────────


class GraphYamlRequest(BaseModel):
    yaml: str


@app.post("/graph/preview")
def api_graph_preview(body: GraphYamlRequest) -> dict[str, Any]:
    """Validate a graph YAML without saving.

    Parses the YAML content and returns a preview with node/edge counts
    and validation status. Used by the external AI graph generator interface.
    """
    import yaml as _yaml

    try:
        raw = _yaml.safe_load(body.yaml)
    except _yaml.YAMLError as e:
        return {
            "valid": False,
            "package_id": "",
            "name": "",
            "node_count": 0,
            "edge_count": 0,
            "nodes": [],
            "edges": [],
            "errors": [f"YAML parse error: {str(e)}"],
        }

    if not isinstance(raw, dict):
        return {
            "valid": False,
            "package_id": "",
            "name": "",
            "node_count": 0,
            "edge_count": 0,
            "nodes": [],
            "edges": [],
            "errors": ["YAML must be a mapping (key-value pairs)"],
        }

    errors: list[str] = []

    # Validate manifest fields
    package_id = str(raw.get("package_id", ""))
    name = str(raw.get("name", ""))
    version = str(raw.get("version", ""))
    author = str(raw.get("author", ""))

    if not package_id.strip():
        errors.append("Missing required field: package_id")
    if not name.strip():
        errors.append("Missing required field: name")
    if not version.strip():
        errors.append("Missing required field: version")

    # Validate nodes
    nodes_raw = raw.get("nodes", [])
    if not isinstance(nodes_raw, list):
        errors.append("'nodes' must be a list")
        nodes_raw = []

    nodes: list[dict] = []
    node_ids: set[str] = set()
    for i, n in enumerate(nodes_raw):
        if not isinstance(n, dict):
            errors.append(f"Node[{i}]: must be a mapping")
            continue
        nid = str(n.get("id", ""))
        ntitle = str(n.get("title", ""))
        ndesc = str(n.get("description", ""))
        if not nid.strip():
            errors.append(f"Node[{i}]: missing 'id'")
        elif nid in node_ids:
            errors.append(f"Node[{i}]: duplicate id '{nid}'")
        else:
            node_ids.add(nid)
        if not ntitle.strip():
            errors.append(f"Node[{i}] '{nid}': missing 'title'")
        if not ndesc.strip():
            errors.append(f"Node[{i}] '{nid}': missing 'description'")
        nodes.append({
            "id": nid,
            "title": ntitle,
            "type": str(n.get("type", "")),
            "difficulty": str(n.get("difficulty", "")),
        })

    # Validate edges
    edges_raw = raw.get("edges", [])
    if not isinstance(edges_raw, list):
        errors.append("'edges' must be a list")
        edges_raw = []

    edges: list[dict] = []
    for i, e in enumerate(edges_raw):
        if not isinstance(e, dict):
            errors.append(f"Edge[{i}]: must be a mapping")
            continue
        efrom = str(e.get("from", ""))
        eto = str(e.get("to", ""))
        erel = str(e.get("relation", ""))
        if not efrom.strip():
            errors.append(f"Edge[{i}]: missing 'from'")
        elif efrom not in node_ids:
            errors.append(f"Edge[{i}]: 'from' references unknown node '{efrom}'")
        if not eto.strip():
            errors.append(f"Edge[{i}]: missing 'to'")
        elif eto not in node_ids:
            errors.append(f"Edge[{i}]: 'to' references unknown node '{eto}'")
        if erel not in VALID_RELATIONS:
            errors.append(
                f"Edge[{i}]: unknown relation '{erel}'. "
                f"Must be one of: {', '.join(sorted(VALID_RELATIONS))}"
            )
        edges.append({"from": efrom, "to": eto, "relation": erel})

    valid = len(errors) == 0

    return {
        "valid": valid,
        "package_id": package_id,
        "name": name,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "errors": errors,
    }


class GraphSaveRequest(BaseModel):
    yaml: str
    package_id: str


@app.post("/graph/save")
def api_graph_save(body: GraphSaveRequest) -> dict[str, Any]:
    """Save a validated graph YAML to the graphs/ directory.

    Creates the directory structure with manifest.yaml and graph.yaml.
    Only saves if the graph passes validation.
    """
    import yaml as _yaml

    safe_id = body.package_id.replace("/", "-").replace("\\", "-").replace(" ", "_").strip()
    if not safe_id:
        raise HTTPException(status_code=400, detail="package_id must not be empty")

    # Validate path safety (resolve against project root, not CWD)
    target_dir = os.path.normpath(os.path.join(_SAFE_PREFIX, safe_id))
    if not target_dir.startswith(_SAFE_PREFIX + os.sep) and target_dir != _SAFE_PREFIX:
        raise HTTPException(status_code=400, detail="Invalid package_id: path traversal detected")

    # Parse YAML
    try:
        raw = _yaml.safe_load(body.yaml)
    except _yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"YAML parse error: {e}")

    if not isinstance(raw, dict):
        raise HTTPException(status_code=400, detail="YAML must be a mapping")

    # Extract fields
    package_id = str(raw.get("package_id", safe_id))
    name = str(raw.get("name", safe_id))
    version = str(raw.get("version", "1.0.0"))
    author = str(raw.get("author", ""))

    nodes_raw = raw.get("nodes", [])
    edges_raw = raw.get("edges", [])

    # Quick validation to ensure basic correctness
    if not isinstance(nodes_raw, list) or len(nodes_raw) == 0:
        raise HTTPException(status_code=400, detail="Graph must have at least one node")
    if not isinstance(edges_raw, list):
        raise HTTPException(status_code=400, detail="'edges' must be a list")

    # Create directory
    os.makedirs(target_dir, exist_ok=True)

    # Write manifest.yaml
    manifest = {
        "package_id": package_id,
        "name": name,
        "version": version,
    }
    if author:
        manifest["author"] = author
    with open(os.path.join(target_dir, "manifest.yaml"), "w", encoding="utf-8") as f:
        _yaml.dump(manifest, f, allow_unicode=True, sort_keys=False)

    # Write graph.yaml
    graph_data = {"nodes": nodes_raw, "edges": edges_raw}
    with open(os.path.join(target_dir, "graph.yaml"), "w", encoding="utf-8") as f:
        _yaml.dump(graph_data, f, allow_unicode=True, sort_keys=False)

    return {
        "status": "saved",
        "package_id": package_id,
        "name": name,
        "path": f"graphs/{safe_id}/",
        "node_count": len(nodes_raw),
        "edge_count": len(edges_raw),
        "reload": {
            "endpoint": "POST /graph/load",
            "body": {"path": f"graphs/{safe_id}/", "package_id": package_id},
            "link": f"Refresh package catalog (GET /graphs/packages), then POST /graph/load {{\"path\": \"graphs/{safe_id}/\"}} to start learning.",
        },
    }


# ── Score / Self-Assessment ───────────────────────────────────────────


@app.post("/nodes/{node_id}/score")
def api_node_score(
    node_id: str,
    score_delta: int = 5,
    description: str = "",
) -> dict[str, Any]:
    """Add a self-assessment score event to a node.

    Accumulates score and auto-promotes to MASTERED when total >= 80
    and the node is COMPLETED.
    """
    rt = _get_runtime()
    try:
        msg = rt.add_score_event(node_id, score_delta, description)
        return {"status": "ok", "message": msg}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {e}") from e


@app.get("/score/presets")
def api_score_presets() -> dict[str, Any]:
    """Return the default recommended score presets."""
    from los.state.models import DEFAULT_SCORE_PRESETS

    return {"presets": DEFAULT_SCORE_PRESETS}


# ── Custom Scoring Dimensions ────────────────────────────────────────


@app.post("/nodes/{node_id}/custom_dims")
def api_node_set_custom_dim(
    node_id: str,
    body: CustomDimRequest,
) -> dict[str, Any]:
    """Set or update a custom scoring dimension for a node.

    Body: { dim_name: str (non-empty, <=32 chars), score: int (0-100) }
    """
    rt = _get_runtime()
    try:
        msg = rt.add_custom_dim_score(node_id, body.dim_name, body.score)
        ns = rt._state.get_node_state(node_id)
        return {
            "status": "ok",
            "message": msg,
            "custom_dims": dict(ns.custom_dims) if ns else {},
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.delete("/nodes/{node_id}/custom_dims/{dim_name}")
def api_node_remove_custom_dim(
    node_id: str,
    dim_name: str,
) -> dict[str, Any]:
    """Remove a custom scoring dimension from a node."""
    rt = _get_runtime()
    try:
        msg = rt.remove_custom_dim(node_id, dim_name)
        ns = rt._state.get_node_state(node_id)
        return {
            "ok": True,
            "message": msg,
            "custom_dims": dict(ns.custom_dims) if ns else {},
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ── Recommendations (Phase 9) ────────────────────────────────────────


@app.get("/recommendations")
def api_recommendations(strategy: str = "next_available") -> dict[str, Any]:
    from los.engine.recommender import (
        recommend_next_available,
        recommend_weak_areas,
        recommend_difficulty_sequence,
        recommend_optimal_path,
    )

    rt = _get_runtime()

    if strategy == "next_available":
        nodes = recommend_next_available(rt)
        return {"strategy": "next_available", "recommendations": nodes}

    if strategy == "weak_areas":
        weak = recommend_weak_areas(rt)
        return {"strategy": "weak_areas", "recommendations": weak}

    if strategy == "by_difficulty":
        nodes = recommend_difficulty_sequence(rt)
        return {"strategy": "by_difficulty", "recommendations": nodes}

    if strategy == "optimal_path":
        return {
            "strategy": "optimal_path",
            "recommendations": [],
            "hint": "use ?target=<node_id>",
        }

    raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy}")


# ── Search ────────────────────────────────────────────────────────────


@app.get("/search")
def api_search(q: str = "") -> dict[str, Any]:
    """Fuzzy search nodes by title or description."""
    if not q or len(q.strip()) < 1:
        return {"query": q, "results": []}

    rt = _get_runtime()
    q_lower = q.lower().strip()
    results = []
    all_ids = rt.get_node_ids()
    for nid in all_ids:
        detail = rt.get_node_detail(nid)
        if detail is None:
            continue
        title = detail.get("title", "").lower()
        desc = detail.get("description", "").lower()
        if q_lower in title or q_lower in desc:
            results.append({
                "id": nid,
                "title": detail["title"],
                "description": detail["description"][:120],
                "type": detail["type"],
                "difficulty": detail["difficulty"],
                "status": detail["status"],
                "match": "title" if q_lower in title else "description",
            })

    return {"query": q, "results": results}


# ── Path / Task Mode ───────────────────────────────────────────────────


@app.get("/path/{target_id}")
def api_path_to(target_id: str) -> dict[str, Any]:
    """Find the optimal learning path to a target node.

    Uses BFS from currently available nodes to find the shortest path
    through the prerequisite graph. For locked (unreachable) targets,
    also returns the full chain of prerequisites needed.
    """
    from los.engine.recommender import recommend_optimal_path

    rt = _get_runtime()
    result = recommend_optimal_path(rt, target_id)

    def _enrich(node_ids: list[str]) -> list[dict[str, Any]]:
        enriched = []
        for nid in node_ids:
            detail = rt.get_node_detail(nid)
            if detail:
                enriched.append({
                    "id": nid,
                    "title": detail["title"],
                    "difficulty": detail["difficulty"],
                    "status": detail["status"],
                })
        return enriched

    reachable = result["reachable"]
    direct_path = result["direct_path"]
    pre_path = result["pre_path"]
    full_path = result["full_path"]

    # Backward compat: path = direct_path if reachable else pre_path
    compat_path = direct_path if reachable else pre_path
    steps = len(compat_path)

    response = {
        "target": target_id,
        "reachable": reachable,
        "target_finished": result.get("target_finished", False),
        "target_status": result.get("target_status"),
        "path": _enrich(compat_path),
        "steps": steps,
        "direct_path": _enrich(direct_path),
        "pre_path": _enrich(pre_path),
        "full_path": _enrich(full_path),
    }

    if not reachable and not full_path:
        response["message"] = "No path found — target does not exist in graph"
    elif not reachable:
        response["message"] = "Target is locked — complete the pre_path prerequisites first"

    return response


# ── Export ────────────────────────────────────────────────────────────


@app.get("/export/prompt")
def api_export_prompt(strategy: str = "next_available") -> dict[str, Any]:
    """Generate a standardized prompt for external AI use.

    Integrates current progress, AI recommendations, and graph structure
    into a ready-to-use prompt string.
    """
    from los.engine.recommender import (
        recommend_next_available,
        recommend_weak_areas,
    )

    rt = _get_runtime()
    progress = rt.get_progress()
    info = rt.get_graph_info()
    user_state = rt._state

    # Build prompt sections
    lines = []
    lines.append("# LearningOS 学习进度报告")
    lines.append("")
    lines.append("## 图谱信息")
    lines.append(f"- 名称: {info['package_name']}")
    lines.append(f"- 版本: {info['package_version']}")
    lines.append(f"- 总节点: {info['node_count']} | 总连接: {info['edge_count']}")
    lines.append("")

    lines.append("## 学习进度")
    lines.append(f"- 完成率: {progress['percentage']}% ({progress['completed']}/{progress['total']})")
    lines.append(f"- 已精通: {progress['mastered']} 个节点")
    lines.append(f"- 可学习: {progress['available']} 个节点")
    lines.append(f"- 待解锁: {progress['locked']} 个节点")
    lines.append("")

    # Completed nodes
    completed_nodes = [
        (nid, ns) for nid, ns in user_state.node_states.items()
        if ns.is_completed
    ]
    if completed_nodes:
        lines.append("## 已完成节点")
        for nid, ns in completed_nodes:
            detail = rt.get_node_detail(nid) or {}
            title = detail.get("title", nid)
            status_label = "★ MASTERED" if ns.status.value == "MASTERED" else "✓ COMPLETED"
            lines.append(f"- [{status_label}] {title} (score: {ns.score})")
        lines.append("")

    # Recommendations
    lines.append("## AI 学习建议")
    recs = recommend_next_available(rt)
    if recs:
        lines.append("### 推荐下一步学习")
        for i, nid in enumerate(recs[:5], 1):
            detail = rt.get_node_detail(nid) or {}
            title = detail.get("title", nid)
            diff = detail.get("difficulty", "")
            desc = detail.get("description", "")[:100]
            lines.append(f"{i}. **{title}** [{diff}] — {desc}")
        lines.append("")

    weak = recommend_weak_areas(rt)
    if weak:
        lines.append("### 需要强化的领域")
        for i, nid in enumerate(weak[:3], 1):
            detail = rt.get_node_detail(nid) or {}
            title = detail.get("title", nid)
            lines.append(f"{i}. {title}")
        lines.append("")

    # Prompt instructions
    lines.append("## 使用说明")
    lines.append("以上是用户当前的学习进度报告。请作为AI学习导师，基于此信息：")
    lines.append("1. 分析用户的知识掌握情况")
    lines.append("2. 推荐最优的下一步学习路径")
    lines.append("3. 为薄弱环节提供针对性学习建议")
    lines.append("4. 给出具体的学习资源推荐")

    prompt_text = "\n".join(lines)
    return {
        "prompt": prompt_text,
        "strategy": strategy,
        "format": "markdown",
    }


@app.get("/export/progress")
def api_export_progress() -> dict[str, Any]:
    """Export the full UserState as downloadable JSON."""
    rt = _get_runtime()
    state = rt._state

    from los.storage.adapter import serialize

    return {
        "export_type": "user_progress",
        "schema_version": state.schema_version,
        "graph_id": state.graph_id,
        "graph_version": state.graph_version,
        "user_id": state.user_id,
        "created_at": state.created_at,
        "exported_at": state.updated_at,
        "data": serialize(state),
    }


@app.post("/import/progress")
def api_import_progress(body: dict[str, Any]) -> dict[str, Any]:
    """Import a previously exported UserState.

    Replaces the current runtime state with the imported data.
    Validates the data structure before applying.
    """
    if body.get("export_type") != "user_progress":
        raise HTTPException(status_code=400, detail="Invalid export format: missing export_type")

    data = body.get("data")
    if not data:
        raise HTTPException(status_code=400, detail="Missing 'data' field in import payload")

    from los.storage.adapter import deserialize

    try:
        imported_state = deserialize(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse import data: {e}") from e

    rt = _get_runtime()
    # Validate graph compatibility
    if imported_state.graph_id and imported_state.graph_id != rt._graph.package_id:
        raise HTTPException(
            status_code=400,
            detail=f"Graph mismatch: imported data is from '{imported_state.graph_id}', "
                   f"but current graph is '{rt._graph.package_id}'",
        )

    # Replace state and sync node states
    rt._state = imported_state
    from los.state.engine import sync_node_states
    node_ids = [n.id for n in rt._graph.get_all_nodes()]
    sync_node_states(rt._state, node_ids)
    rt._mutator = type(rt._mutator)(rt._state)
    rt.save()

    progress = rt.get_progress()
    return {
        "status": "imported",
        "message": f"Progress imported: {progress['completed']}/{progress['total']} nodes completed",
        **progress,
    }


# ── Learning Log (Phase ②) ────────────────────────────────────────────


@app.get("/learning-log")
def api_learning_log() -> dict[str, Any]:
    """Return the learning activity log for visualization.

    Aggregates history entries by date and node, returning:
      - daily_summary: {date: {nodes_completed, total_score, xp_earned}}
      - recent_activity: list of recent history entries (last 50)
      - streaks: current and longest daily streak
    """
    from collections import defaultdict

    rt = _get_runtime()
    state = rt._state

    # Aggregate by date
    daily: dict[str, dict[str, int]] = defaultdict(lambda: {"nodes_completed": 0, "total_score": 0})
    seen_nodes: set[str] = set()

    for entry in state.history:
        if entry.field not in ("status", "score"):
            continue
        date = entry.timestamp[:10]  # YYYY-MM-DD
        if entry.field == "status" and entry.new_value in ("COMPLETED", "MASTERED"):
            if entry.node_id not in seen_nodes:
                daily[date]["nodes_completed"] += 1
                seen_nodes.add(entry.node_id)
        elif entry.field == "score":
            try:
                old_s = int(entry.old_value)
                new_s = int(entry.new_value)
                daily[date]["total_score"] += (new_s - old_s)
            except (ValueError, TypeError):
                pass

    # Sort dates
    sorted_dates = sorted(daily.keys())

    # Calculate streaks
    from datetime import datetime, timedelta

    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    today = datetime.now().strftime("%Y-%m-%d")

    for i, date in enumerate(sorted_dates):
        if daily[date]["nodes_completed"] > 0:
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 0

    # Check current streak (from today backwards)
    current_streak = 0
    check_date = today
    for _ in range(365):  # max 1 year lookback
        if daily.get(check_date, {}).get("nodes_completed", 0) > 0:
            current_streak += 1
        elif current_streak > 0:
            break
        check_date = (datetime.strptime(check_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

    # Recent activity (last 30 entries)
    recent = []
    for entry in reversed(state.history[-50:]):
        node = rt._graph.get_node(entry.node_id)
        title = node.title if node else entry.node_id
        recent.append({
            "date": entry.timestamp[:10],
            "time": entry.timestamp[11:19] if len(entry.timestamp) > 11 else "",
            "node_id": entry.node_id,
            "title": title,
            "field": entry.field,
            "old_value": entry.old_value,
            "new_value": entry.new_value,
            "timestamp": entry.timestamp,
            "description": getattr(entry, "description", ""),
        })

    # Build daily summary for chart
    daily_summary = []
    for date in sorted_dates:
        daily_summary.append({
            "date": date,
            "nodes_completed": daily[date]["nodes_completed"],
            "total_score": daily[date]["total_score"],
        })

    return {
        "daily_summary": daily_summary,
        "recent_activity": recent,
        "streaks": {
            "current": current_streak,
            "longest": longest_streak,
        },
        "total_days_active": sum(1 for d in daily.values() if d["nodes_completed"] > 0),
        "total_nodes_completed": state.completed_count,
        "total_xp": state.total_xp,
    }


@app.get("/global-state")
def api_global_state() -> dict[str, Any]:
    """Return cross-graph aggregate state (XP, graph count, etc.)."""
    return _compute_global_state()


@app.get("/export/share")
def api_export_share() -> dict[str, Any]:
    """Export current learning progress as shareable summary."""
    rt = _get_runtime()
    state = rt._state
    info = rt.get_graph_info()
    progress = rt.get_progress()
    global_state = _compute_global_state()

    from los.engine.xp import get_level, xp_to_next_level
    from los.engine.achievements import check_achievements

    ach_results = check_achievements(state, global_state=global_state)
    earned_achs = [
        {"name": a.name, "icon": a.icon}
        for a, ok in ach_results if ok
    ]

    proficiency_counts = {"None": 0, "Done": 0, "Known": 0, "Skilled": 0, "Expert": 0, "Master": 0}
    for ns in state.node_states.values():
        from los.engine.xp import get_proficiency
        prof = get_proficiency(ns.score)
        key = prof.get("label_en", "None")
        if key in proficiency_counts:
            proficiency_counts[key] += 1

    global_xp = global_state["total_xp"]
    level = get_level(global_xp)

    recent_activity = []
    for entry in reversed(state.history[-20:]):
        recent_activity.append({
            "timestamp": entry.timestamp,
            "node_id": entry.node_id,
            "field": entry.field,
            "description": entry.description,
            "old_value": entry.old_value,
            "new_value": entry.new_value,
        })

    return {
        "package_name": info["package_name"],
        "package_id": info["package_id"],
        "progress": progress,
        "proficiency_distribution": proficiency_counts,
        "total_xp": global_xp,
        "level": level,
        "xp_to_next": xp_to_next_level(global_xp),
        "earned_achievements": earned_achs,
        "graphs_loaded": global_state.get("graphs_loaded", 0),
        "graphs_completed": global_state.get("graphs_completed", 0),
        "recent_activity": recent_activity,
        "exported_at": _utc_now_iso(),
    }


@app.post("/graph/reset")
def api_graph_reset() -> dict[str, Any]:
    """Reset current graph's progress data (delete state file and reload)."""
    rt = _get_runtime()
    gid = rt._state.graph_id
    if not gid:
        raise HTTPException(status_code=400, detail="No graph currently loaded")

    from los.state.models import UserState
    from los.storage.adapter import save, state_path_for_graph
    from los.state.engine import sync_node_states

    # Use state_path_for_graph for consistent path resolution (respects LEARNINGOS_DATA_DIR)
    state_file = state_path_for_graph(gid)
    try:
        if os.path.exists(state_file):
            os.remove(state_file)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete state file: {e}") from e

    # Re-initialize the runtime with a fresh state
    try:
        fresh_state = UserState(user_id="default", graph_id=gid)
        fresh_state.graph_id = gid
        # Sync with current graph nodes to create NodeState entries
        node_ids = [n.id for n in rt._graph.get_all_nodes()]
        sync_node_states(fresh_state, node_ids)
        # Save the fresh state
        save(fresh_state, state_file)
        rt._state = fresh_state
        rt._mutator = type(rt._mutator)(rt._state)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error during reset: {e}") from e

    return {"status": "ok", "message": f"Graph '{gid}' data has been reset"}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LearningOS Runtime API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    args = parser.parse_args()

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)
