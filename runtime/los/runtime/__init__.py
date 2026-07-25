# Runtime Authority package.
#
# Owns runtime orchestration, lifecycle coordination, and the capability
# contracts that define what Runtime requires from its providers.
#
# Defined by:
#   RS-006 Runtime Authority Model (Frozen)
#   Implementation Mapping Phase 1 (Frozen)
#   AD-003 Runtime Authority Ownership (Approved)
#   Phase 2 Implementation Contract (Accepted)
#   Phase 4 Persistence & Recovery (Approved)
#
# Note: RuntimeInstance and RuntimeStatus are importable from
# los.runtime.runtime_instance directly.  They are NOT re-exported here
# to avoid a circular import chain:
#   engine.contracts → runtime.contracts → runtime.__init__ → runtime_instance → engine.resolver
#
# RuntimeManifest is safe to re-export — it has no los.* imports beyond los.common.
