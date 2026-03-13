# Diary: FR-195 Philosopher Challenge Node

**Date:** 2026-03-13
**FR:** FR-195
**Theme:** Adversarial Quality Gates

## Reflection

The distill-then-challenge pattern emerged from two Scripture traps meeting in the wild: `false_duplicate` and `unchallenged_premise`. The philosopher graph was accepting every pattern meeting the occurrence threshold without asking "Is the pain real?" — the very Red Hat gap the Scripture identifies.

The interesting trap during implementation was `extract_json`'s array-first search: when the Proposal object contains a `files` array, `extract_json` finds `["file1.md", ...]` before `{...}` because it checks `[` brackets first. This is a boundary normalization issue — the function was designed for analyze output (arrays) and silently produced wrong results for distill output (objects containing arrays). Rather than modify the shared utility and risk breaking callers, I wrote object-first extraction in `unwrap_distill`. The fix follows the Scripture's `callsite_fix` cure: "Fix at the specific caller, not the shared utility."

**Trap:** Shared utility assumptions — a function designed for one shape silently produces wrong results for another. `extract_json`'s array-first search is correct for arrays but breaks for objects containing arrays. The symptom (Pydantic validation error on a list) was far from the cause (wrong JSON boundary detection).

**Heuristic:** When a shared utility fails for a new use case, check whether the failure mode is fundamental (the utility's contract doesn't cover your shape) before patching. If fundamental, write a caller-specific solution rather than generalizing the utility.

**Seed:** Should `extract_json` accept a `prefer` parameter (`"object"` or `"array"`) to make the boundary search order explicit? Or would that be premature generalization — the callsite fix is already clean.
