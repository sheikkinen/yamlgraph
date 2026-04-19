# Reflection: FR-241 Complete Worktree Teardown Self-Heal (2026-04-19)

## Cognitive Trap: CAP/REQ-YG Parallel Collision (recurring)

**Trap**: FR-241 independently assigned CAP-100/REQ-YG-242, which had just been claimed by FR-239 (merged minutes earlier). The pattern recurs every batch of parallel branches.

**Cure**: Merge main before committing any capability YAML. The validator catches it, but cost is one extra CI round-trip.

**Heuristic**: The cap ID collision is proportional to branch count × merge lag. The fix is always the same: rename to next free ID. Automate it.

**Seed**: Could `scripts/next_cap_id.py` be a one-liner helper that reads the registry and prints the next available CAP-N and REQ-YG-N, called at FR creation time by the Chaplain?
