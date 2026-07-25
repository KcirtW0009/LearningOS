"""LearningOS exception hierarchy.

All LOS-specific errors inherit from LOSError.
Callers (CLI, future API) can catch LOSError for any LOS failure
or catch specific subclasses for targeted handling.
"""


class LOSError(Exception):
    """Base exception for all LearningOS errors."""
    pass


# ── Graph errors ───────────────────────────────────────────────────────

class GraphError(LOSError):
    """Base for graph loading and validation failures."""
    pass


class GraphNotFoundError(GraphError):
    """A required file or package path does not exist."""
    pass


class GraphParseError(GraphError):
    """Graph data is malformed (bad YAML, missing required fields)."""
    pass


class GraphValidationError(GraphError):
    """Graph structure is invalid (duplicate IDs, broken references)."""
    pass


# ── State errors ───────────────────────────────────────────────────────

class StateError(LOSError):
    """Base for state transition and node lookup failures."""
    pass


class NodeNotFoundError(StateError):
    """Requested node_id is not tracked in UserState."""
    pass


class InvalidStateTransitionError(StateError):
    """Attempted status transition violates the state machine."""
    pass


class NodeAlreadyCompletedError(StateError):
    """Attempted to complete a node that is already COMPLETED or MASTERED."""
    pass


# ── Storage errors ─────────────────────────────────────────────────────

class StorageError(LOSError):
    """Base for persistence failures."""
    pass


class SchemaVersionError(StorageError):
    """Stored data has an incompatible or missing schema_version."""
    pass


class RecoveryError(LOSError):
    """Runtime Instance recovery failed — data missing or corrupted."""
    pass
