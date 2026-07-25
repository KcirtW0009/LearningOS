"""Graph data models — Node, Edge and Resource dataclasses.

Defined by:
  - LOS-0301 Node Model
  - LOS-0302 Edge Model
  - LOS-0305 Graph Package Schema
  - RES-001 Resource Model (Phase 6)
"""

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Resource (Phase 6)
# ---------------------------------------------------------------------------

VALID_RESOURCE_TYPES: frozenset[str] = frozenset({"url", "file", "markdown"})


@dataclass(frozen=True)
class Resource:
    """A learning resource linked to a Node.

    Fields:
        type  — resource kind (url / file / markdown)
        uri   — resource location or inline content
        label — human-readable name for this resource (e.g. "官方文档")
    """

    type: str
    uri: str
    label: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.type or not self.type.strip():
            raise ValueError("Resource.type must not be empty")
        if self.type not in VALID_RESOURCE_TYPES:
            raise ValueError(
                f"Unknown Resource type '{self.type}'. "
                f"Must be one of: {', '.join(sorted(VALID_RESOURCE_TYPES))}"
            )
        if not self.uri or not self.uri.strip():
            raise ValueError("Resource.uri must not be empty")


# ---------------------------------------------------------------------------
# Relation type constants (LOS-0302, LOS-0305)
# ---------------------------------------------------------------------------

# All recognized relation types — canonical definition.
# graph/loader.py and graph/validator.py import this instead of maintaining
# their own copies.
VALID_RELATIONS: frozenset[str] = frozenset(
    {"prerequisite", "dependency", "progression", "association", "alternative"}
)

# Relations that affect Node availability (source completed → target unlocked)
_BLOCKING_RELATIONS: frozenset[str] = frozenset(
    {"prerequisite", "dependency", "progression"}
)


def is_blocking_relation(relation: str) -> bool:
    """Return True if this relation affects Node availability."""
    return relation in _BLOCKING_RELATIONS


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Node:
    """The fundamental unit of a Learning Graph.

    A Node represents an individual learning element: a concept, skill,
    project, milestone, or achievement.

    Required fields (LOS-0301, LOS-0305):
        id          — globally unique Node identifier (lowercase, hyphen-separated)
        title       — human-readable name
        description — explanation of what this Node represents

    Optional fields (LOS-0301, LOS-0305):
        type       — semantic classification (concept, skill, project, milestone)
        difficulty — learning complexity (beginner, intermediate, advanced)
    """

    id: str
    title: str
    description: str
    type: Optional[str] = None
    difficulty: Optional[str] = None
    resources: list = field(default_factory=list)
    """Learning resources linked to this Node (list of Resource)."""

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("Node.id must not be empty")
        if not self.title or not self.title.strip():
            raise ValueError("Node.title must not be empty")
        if not self.description or not self.description.strip():
            raise ValueError("Node.description must not be empty")


# ---------------------------------------------------------------------------
# Edge
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Edge:
    """A directed relationship between two Nodes.

    Required fields (LOS-0302, LOS-0305):
        source   — source Node ID (YAML key: "from")
        target   — target Node ID (YAML key: "to")
        relation — semantic meaning of the relationship

    Recognised relation types (LOS-0305):
        prerequisite — source must be completed before target
        dependency   — target depends on source (same semantics as prerequisite)
        progression  — natural learning sequence
        association  — related concept (does NOT affect availability)
        alternative  — alternative learning path (does NOT affect availability)

    The Python attribute is named ``source`` (not ``from``) because ``from``
    is a reserved keyword.  YAML serialisation maps ``"from"`` → ``source``.
    """

    source: str
    target: str
    relation: str

    def __post_init__(self) -> None:
        if not self.source or not self.source.strip():
            raise ValueError("Edge.source must not be empty")
        if not self.target or not self.target.strip():
            raise ValueError("Edge.target must not be empty")
        if not self.relation or not self.relation.strip():
            raise ValueError("Edge.relation must not be empty")
