"""RuntimeManifest — persisted identity and binding metadata for RuntimeInstance.

Defined by:
  - RS-001 Runtime Graph Instance Model (Frozen)
  - RS-006 Runtime Authority Model (Frozen)
  - Phase 4 Implementation Contract (Approved)

Ownership:
    Runtime Authority (los/runtime/).

    RuntimeManifest represents the persisted identity of a RuntimeInstance.
    It does NOT belong to State Authority, Storage Layer, or Session Layer.

Persistence:
    The Storage Adapter persists RuntimeManifest as a plain dict (JSON).
    Storage never imports RuntimeManifest — it operates on dicts only.
    The serialization bridge (to_dict / from_dict) lives here, inside
    the Runtime package.

File:
    data/runtime-manifest.json
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from los.common import utc_now_iso

# Default filesystem location for the manifest JSON file.
DEFAULT_MANIFEST_PATH: str = "data/runtime-manifest.json"


@dataclass
class RuntimeManifest:
    """Persisted identity and binding metadata for one RuntimeInstance.

    Fields (frozen by Phase 4 Implementation Contract):
        runtime_id    — unique identity (RS-001 Contract 1)
        graph_path    — filesystem path to the bound Graph Package
        graph_id      — identity of the bound Graph Package
        graph_version — version of the bound Graph Package
        created_at    — ISO-8601 timestamp of RuntimeInstance creation
        last_active   — ISO-8601 timestamp of last activity (updated on save)
    """

    runtime_id: str
    graph_path: str
    graph_id: str = ""
    graph_version: str = ""
    created_at: str = ""
    last_active: str = ""

    def __post_init__(self) -> None:
        now = utc_now_iso()
        if not self.created_at:
            self.created_at = now
        if not self.last_active:
            self.last_active = now

    # ── serialization (dict boundary — Storage sees only dict) ──────────

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict for storage persistence.

        The Storage Adapter calls this indirectly: RuntimeInstance converts
        RuntimeManifest → dict, then passes the dict to storage.
        """
        return {
            "runtime_id": self.runtime_id,
            "graph_path": self.graph_path,
            "graph_id": self.graph_id,
            "graph_version": self.graph_version,
            "created_at": self.created_at,
            "last_active": self.last_active,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RuntimeManifest:
        """Deserialize from a plain dict returned by storage."""
        return cls(
            runtime_id=d.get("runtime_id", ""),
            graph_path=d.get("graph_path", ""),
            graph_id=d.get("graph_id", ""),
            graph_version=d.get("graph_version", ""),
            created_at=d.get("created_at", ""),
            last_active=d.get("last_active", ""),
        )
