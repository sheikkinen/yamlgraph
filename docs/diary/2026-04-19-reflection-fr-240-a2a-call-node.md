# Reflection: FR-240 A2A Call Node Type (2026-04-19)

## Cognitive Trap: CAP/REQ-YG Parallel Collision

**Trap**: Every branch developed independently assigns the next free CAP/REQ-YG ID. When multiple branches are in flight simultaneously, they independently pick the same number (CAP-96, REQ-YG-239 in this case).

**Cure**: The capability registry validator catches this at pre-commit and CI. The resolution pattern is deterministic: merge main first, then rename the branch's ID to next free beyond all currently taken.

**Insight**: CAP numbering is a shared mutable counter accessed by concurrent branches — the classic distributed systems problem of ID generation without coordination. The current approach (manual rename on collision) works but degrades as branches multiply.

**Seed**: Could the Chaplain auto-assign CAP/REQ-YG IDs at FR creation time by reading the registry, preventing collisions before any branch is cut?
