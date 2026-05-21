# Reflection: FR-440 Pipe-Buffer Guard

**Date:** 2026-05-21
**FR:** FR-440

## Trap: instruction_boundary_uncrossed

The anti-pattern `pytest | tail` was already documented in user memory (`pytest-pipe-buffering.md`) — a personal note visible to the agent but not enforced at the project level. The insight existed but lived in the wrong enforcement layer: advisory memory instead of a mechanical gate. Advisory knowledge without enforcement is decoration. The 13 audit log occurrences prove agents re-derive the bad pattern from their system prompt's generic "use head/tail to limit output" instruction, overriding any advisory knowledge.

## Heuristic: detection_without_enforcement

If a known anti-pattern has documentation but no gate, count occurrences in the audit log. If count > 3, the documentation has failed — graduate to enforcement. The audit log is the ground truth for whether advisory controls work.

## Seed:

What other patterns in user memory or copilot-instructions are purely advisory but have measurable violation rates in the audit log? A systematic scan of `audit.jsonl` against known guidelines could surface the next enforcement candidate automatically.
