# Judgement: FR-1063 Map compiler package split

**Prior art:** `FR-1063-map-compiler-package-split.md` is the FR this judgement governs. FR-1057 (prompt template dialect split) matches only on "split"; it splits a prompt dialect, not a compiler module.

**Verdict:** REJECTED — the move is plausible, but this newly filed FR lacks substantive committed research under the prospective FR-890 gate; no implementation authority is granted.

**Reviewed against:** `feature-requests/FR-1063-map-compiler-package-split.md`; `feature-requests/FR-936-map-node-hardening.judgement.md`; `docs/issues-2026-09-24.md`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The first consumer and size pressure are concrete (FR-1063:8-14, 32-45; plan section 6.5). A move-only package refactor ahead of a behavior change is independently testable. The five proposed modules have distinct responsibilities (FR-1063:55-72). Classification: maintenance of an existing framework primitive, not a new capability; the cited FR-936 split concerns behavior, not this move (FR-1063:18-20).

## Required revisions

### R-1: Re-file with substantive research

In a new FR, commit a research record with four to six genuine solution classes for the module-size/change-rate problem, including the selected one, precedent for each, preserved dissent, and an explicit `is_this_a_graph` answer. FR-1063:91-98 rejects four variants of the same refactor without precedent or the graph-fit answer. The source-reading link does not supply those missing comparisons (plan section 6.5). The active gate requires no authority for this file (judge doctrine, Local conventions).

### R-2: Preserve behavior at the import boundary

In the replacement, enumerate every importer and patch target before deleting the old module, and assert equivalent return values for `wrap_for_reducer` on dict, non-dict, and error paths. The promised shared normalization and typed return record change code beyond a literal move (FR-1063:64-78); green existing tests alone do not prove equivalence across those paths. Do not fold FR-1064's join or failure behavior into this refactor.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Rejected FR-1063 disposition and a separately filed, researched replacement plan only |

Not authorized: moving or deleting `yamlgraph/compile/map_compiler.py`, changing tuple consumers, adding `CompiledMap`, modifying map execution, or changing tests under FR-1063.

## Revised acceptance criteria

- [ ] AC-01: A replacement FR cites committed research comparing four to six genuine solution classes with precedent, dissent, and `is_this_a_graph`.
- [ ] AC-02: The replacement lists importers and patch targets and specifies assertions for all three result shapes before approving any move.
- [ ] AC-03: FR-1063 remains Rejected and the replacement has its own judgement before implementation.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No production or test edits under this rejected FR; a new researched FR must be judged independently. | GATE |
| C-2 | A replacement refactor must not change map failure or retry semantics. | GATE |

Authority granted: none under FR-1063.
