# FR-489: DM v2 — `session.py` Refactor (Compose Dedup + Navigation Extraction)

**Priority:** LOW
**Type:** Refactor (DM v2 prototype; inherits FR-474 J3/J4 regime)
**Status:** Done (2026-06-15). **Both phases shipped.** Phase 1 deduped the
composed-stage dispatch; Phase 2 extracted pure navigation to `api/navigation.py`
(roster expansion lifted into `accept()`), dropping `session.py` to 397 lines.
Witnessed below.
**Effort:** Phase 1 ~0.1 day (done); Phase 2 ~0.3 day (done)
**Requested:** 2026-06-15
**Continues:** FR-475 (the stage tree + roster pattern), FR-477/484/485/487 (the
composed turn + finish stages). Same J3 rules: **no CAP/REQ, no CI gate, no
demo-log**; the prototype tests under `examples/dungeon_master/tests/` are the
visibility harness. Behaviour-preserving — the 45-test suite is the contract.

**Model under test:** `vertex` / `gemini-3.5-flash`.

## Summary

`api/session.py` crossed the CLAUDE.md size guidance (target < 400, max 450) at
**485 lines** while still growing — FR-488 (book-scope chapters) would add a fifth
composed-stage branch and a second roster-expansion path. Refactor it in two
behaviour-preserving phases, each green against the existing suite:

- **Phase 1 — Compose dedup (done).** Collapse the duplicated composed-stage
  dispatch shared by `weave` and `_autodraft` into one `_compose_special` helper.
- **Phase 2 — Navigation extraction (proposed).** Move the tree-navigation cluster
  (reachability + landing) out of `DMSession` to sit beside the tree model it
  reasons about, dropping the file under 400 lines.

## Value Statement

The adapter stays legible and under the size budget as book scope lands: the
"which node is reachable / where do we land next" logic lives next to the tree it
queries, and the "how is a composed stage drafted" logic exists once — so FR-488's
chapter stage extends one branch and one expansion path, not two of each.

## Problem

Two distinct growth pressures, both visible before FR-488:

1. **Duplicated composed-stage dispatch.** The four-way branch that drafts the
   composed stages — a play `turn` (re-rolls intents + recap, FR-477 J2), the
   continuous `final_cut` (FR-484), the turn-structured `final_cut_turns`
   (FR-485), and the `walkthrough` (FR-487) — each setting `text` plus a
   structured `turns`/`setting` track — existed **verbatim in two methods**:
   `weave` (instruction/draft steer it) and `_autodraft` (fresh, empty args). The
   only difference between the copies was whether a writer's instruction steered
   the composition. A fifth composed stage (chapters) would have to be added to
   both copies, in lockstep — the classic shotgun-surgery duplication.

2. **File over the size budget.** At 485 lines `session.py` exceeds the max-450
   guidance. The largest non-action cluster is tree navigation — `_can_visit`,
   `_accept_target`, `_next_unreviewed_char`, `_expand_roster`, `_characters` —
   which reasons about *tree* properties (parent-reviewed gates, roster
   resolution, landing order) yet lives in the session adapter, far from the
   `tree.py` model it queries.

## Proposed Solution

### Phase 1 — Compose dedup (DONE)

Extract the shared dispatch into one method on `DMSession`:

```python
async def _compose_special(
    self, doc, entry, stage, *, instruction: str, draft: str
) -> bool:
    """Draft a composed multi-layer stage (a turn or one of the three finishes).

    weave and _autodraft share this exact dispatch — the only difference is
    whether a writer's instruction/draft steers it (weave) or it is a fresh
    draft (auto-draft, empty args). Mutates entry in place; returns whether the
    stage was a composed stage, so the caller falls back to _invoke_stage for an
    ordinary card when it was not.
    """
```

Both call sites collapse to:

```python
if not await self._compose_special(doc, entry, stage, instruction=prompt, draft=text):
    entry["text"] = await self._invoke_stage(doc, stage, text, prompt)
```

`weave` keeps the empty-generation decline guard (Commandment 6) after the call;
`_autodraft` keeps its `reviewed=False` + persist after it. No test changed.

**Result:** 485 → 482 lines; the four-branch block exists once; FR-488 adds one
`chapters` branch in one place. 45 tests green, ruff clean.

### Phase 2 — Navigation extraction (PROPOSED)

Move the tree-navigation cluster to live with the tree model. Candidate new home:
`api/navigation.py` (or extend `tree.py`), holding pure functions that take
`doc` + the characters accessor:

- `can_visit(doc, target) -> bool` (was `_can_visit`)
- `accept_target(doc, stage, *, expand_roster) -> str | None` (was `_accept_target`)
- `next_unreviewed_char(doc, after=None) -> str | None` (was `_next_unreviewed_char`)

`DMSession` keeps thin wrappers that bind the session's `_characters`,
`_expand_roster`, and `_invoke_stage` — i.e. the *side-effecting* parts (graph
invocation, roster expansion) stay in the adapter; the *pure tree reasoning* moves
out. The lone entanglement is one line: `_accept_target`'s synopsis branch calls
`await self._expand_roster(...)`. The Judgement resolves it (below) by lifting that
side-effect into `accept()`, leaving `accept_target` pure.

**Target:** `session.py` < 400 lines; `navigation` module is pure + directly
unit-testable without a session.

## Judgement (2026-06-15)

**Phase 1 — APPROVED, frozen.** The `_compose_special` extraction is
behaviour-preserving (45 tests green, ruff clean), collapses verbatim duplication,
and makes FR-488's chapter branch a one-line addition. No changes required.

**Phase 2 — APPROVED with scope refined to eliminate the open question.** The FR
left "move `accept_target` whole vs. only the two pure functions" open and hedged
with "start with two, measure, then decide." That hedge is indecision; the code
shows the entanglement is a single line, so the path is explicit:

- **J1 — Split `_accept_target`; do not pass a callback.** The pure landing
  decision `accept_target(doc, stage) -> str | None` moves to `navigation`. Its
  one side-effect — the synopsis-accept roster expansion — is *lifted out* into
  `accept()`, which calls `_expand_roster` when the accepted stage is the
  synopsis, then asks `accept_target` for the landing node. Threading
  `_expand_roster` through navigation as a callback is rejected: it smuggles a
  graph-invoking side-effect through a module whose value is being pure.
- **J2 — Move all three in one commit, not staged.** With J1 making
  `accept_target` pure, `can_visit`, `accept_target`, and `next_unreviewed_char`
  are all pure functions of `doc`; there is no reason to stage them or "measure."
  One Phase-2 commit moves the cluster.
- **J3 — Navigation functions must not mutate `doc`.** They read the characters
  sub-doc through a pure reader, not the mutating `setdefault` accessor. The
  mutating `_characters` stays in the adapter (it is a write path); navigation
  gets a read-only view (e.g. `doc.get("characters", {})`).
- **J4 — New module `api/navigation.py`, not extending `tree.py`.** `tree.py` is
  the *static* stage model (the `STAGES` tuple, `resolve_stage`); navigation is
  *doc-dependent* reachability and landing — a different concern that would bloat
  `tree.py` and blur its role.
- **J5 — Acceptance is the test suite plus a direct unit test.** All three pure
  functions get a unit test that needs no `DMSession` (the payoff of the move);
  `session.py` < 400; import-linter clean.

Scope frozen to the above. The OQ paragraph below is superseded.

## Acceptance Criteria

- [x] Phase 1: `_compose_special` extracted; `weave` and `_autodraft` share it.
- [x] Phase 1: 45 prototype tests green; ruff check + format clean.
- [x] Phase 1: decline guard and auto-draft persist semantics unchanged.
- [x] Phase 2: `can_visit`, `accept_target`, `next_unreviewed_char` moved to
      `api/navigation.py` as pure functions of `doc` (no mutation) (J1–J4).
- [x] Phase 2: `_accept_target`'s synopsis roster expansion lifted into `accept()`;
      no side-effect threaded through navigation (J1).
- [x] Phase 2: `session.py` < 400 lines (397).
- [x] Phase 2: 56 prototype tests green (45 + 11 navigation); ruff + import-linter
      clean.
- [x] Phase 2: all three navigation functions covered by direct unit tests that
      need no `DMSession` (`tests/test_navigation.py`, J5), incl. a purity guard
      asserting `doc` is never mutated (J3).

## Alternatives Considered

- **One mega-extraction in a single commit.** Rejected: mixes the safe pure dedup
  with the riskier boundary move; two phases keep each diff one-concern and
  separately revertable (Scripture: one concern per commit).
- **Leave it over budget until FR-488.** Rejected: FR-488 would double the
  composed-stage branch and the roster-expansion path; dedup first makes that
  feature a one-line addition, not a two-place edit.
- **Promote navigation into `turn_ops`.** Rejected: `turn_ops` owns play-turn
  composition, not tree reachability; navigation belongs with `tree`.

## Related

- FR-475 (stage tree + roster), FR-477/484/485/487 (composed stages)
- FR-488 (book-scope chapters — the feature this refactor unblocks)
- CLAUDE.md module-size guidance (target < 400, max 450)
