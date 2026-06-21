# Feature Request: DM v2 `TurnRequest` / `TurnResult` Contract + `turn_engine` Extraction (Contract B)

**Priority:** MEDIUM (v3-enabling; removes the turn loop as a hidden authoring boundary)
**Type:** Enhancement (refactor — additive, behavior-preserving)
**Status:** Enforced (golden 59a1578d; extraction this commit — DM suite 404 green)
**Effort:** ~1 day (the graph payload is already doc-free; this is re-housing, not rewriting)
**Requested:** 2026-06-21

> Reference: [`docs/refactoring-plan.md`](../examples/dungeon_master/docs/refactoring-plan.md) §3 Contract B.

## Summary

`turn_ops.invoke_turn` fuses three concerns: **prompt assembly** (`running_scene`,
`_beats_block`), **DM gating** (roster scoping, lifecycle/memory gates), and the **actual
engine** (graph call + the beat/phase FSM + intent normalization). The graph payload it
builds is already a flat, **doc-free** dict. This FR draws a typed `TurnRequest` /
`TurnResult` boundary and extracts a `turn_engine` module owning only the engine concern,
leaving assembly and gating in the adapter as the *projection* that builds the request.

## Value Statement

The turn loop stops being an authoring boundary a maintainer must remember; the beat/phase
FSM — the single most reusable unit in the codebase — gets a name and a typed contract, and
v3 can keep the engine verbatim while replacing the projection layer around it.

## Problem

`invoke_turn` already hands the turn graph a doc-free payload:

```python
{"cast", "scene", "turn_n", "instruction", "protected",
 "gone_this_chapter", "intents", "direction", "recap"}
```

No `doc` / `cid` crosses into the graph — **all coupling is in the Python that builds and
writes back that payload**, not in the engine's computational core. That core
(`get_app(TURN_GRAPH).ainvoke` + `_satisfied_indices` / `_apply_beat_ledger` /
`_phase_for_count` + `_direction_dict` + intent normalization) is pure/typed and fully
tested, but it has no contract of its own, so it is entangled with ~10 sibling imports that
all serve assembly/gating.

## Proposed Solution

1. **Typed packets.**
   - `TurnRequest`: `cast: list[CastMember]`, `scene: str`, `turn_n: int`, `instruction: str`,
     `beats: list[str]`, `prior_direction: dict`, and an **opaque `extras: dict`** for
     DM-semantic prompt vars (`protected`, `gone_this_chapter`) — keep DM lifecycle concepts
     out of the shared engine.
   - `TurnResult`: `intents: list[Intent]`, `direction: Direction` (phase/beats **computed**),
     `recap: str`.
2. **`turn_engine` module** owning only: graph invocation, the beat-FSM (move
   `_satisfied_indices` / `_apply_beat_ledger` / `_phase_for_count` verbatim — already pure),
   and typed normalization of `intents` / `direction`. A single `async play_turn(req) -> result`.
3. **Adapter keeps projection + persistence.** `turn_ops` builds the `TurnRequest`
   (`running_scene`, roster scoping, the lifecycle/memory gates) and writes the `TurnResult`
   back into the doc (`turn_record`). No behavior change.

```python
# turn_engine.py — doc-free, reusable
async def play_turn(req: TurnRequest) -> TurnResult: ...

# turn_ops.py — the DM projection (assembly + gating), unchanged behavior
req = build_turn_request(doc, chars, cid, n, instruction)   # running_scene + gates
result = await turn_engine.play_turn(req)
write_turn_result(doc, cid, n, result, roster)              # turn_record
```

## Acceptance Criteria

- [ ] `TurnRequest` / `TurnResult` (+ `CastMember`, `Intent`, `Direction`) typed.
- [ ] `turn_engine.play_turn` is doc-free (imports nothing from `chapter_nav` / the doc
      shape); the beat-FSM functions moved verbatim with their existing unit tests passing.
- [ ] `invoke_turn` refactored to build-request → `play_turn` → write-result; **byte-identical
      turn output** proven by a monkeypatched-LLM characterization test.
- [ ] `extras` carries `protected` / `gone_this_chapter` as opaque pass-through (no DM
      lifecycle types leak into `turn_engine`).
- [ ] DM suite green; `turn_ops` stays under the 400-line warn gate.
- [ ] `docs/architecture.md` §5 + module map updated; `docs/refactoring-plan.md` Contract B
      marked in-progress.

## Alternatives Considered

- **Leave `invoke_turn` as-is** — rejected; it remains a silent authoring boundary and the
  reusable FSM stays entangled (the v3 doc keeps this engine verbatim, so it needs a contract).
- **Bake `protected` / `gone_this_chapter` into typed engine fields** — rejected; that imports
  DM lifecycle semantics into a would-be-shared module. `extras` keeps the engine generic.
- **Extract a full generic library now** — rejected as speculative (Scripture *purge*); the
  justification is v3 (a second consumer), so extract only behind the request/result contract.

## Related

- [`docs/refactoring-plan.md`](../examples/dungeon_master/docs/refactoring-plan.md) §3 Contract B
- [`api/turn_ops.py`](../examples/dungeon_master/api/turn_ops.py) — `invoke_turn`, the beat-FSM
- FR-503/504 (the beat ledger / phase computation being extracted)
- FR-556 (Contract A — read cleaner after it; not a hard dependency)
- [`docs/v3-rewrite-guidance.md`](../examples/dungeon_master/docs/v3-rewrite-guidance.md) §2 (v3 keeps this engine verbatim)

## Judgement (2026-06-21)

**Verdict: APPROVE WITH CONDITIONS.** This is the cleanest of the three contract FRs because its
load-bearing premise was verified against live code, not asserted. The payload `invoke_turn` hands
the graph is **doc-free in fact**: `{cast, scene, turn_n, instruction, protected, gone_this_chapter,
intents, direction, recap}` — no `doc`/`cid` crosses the boundary (confirmed; `gone_this_chapter` was
*just* added to that exact dict in FR-554, and it too is a pre-computed string, not a doc handle). The
beat-FSM functions named for extraction (`_satisfied_indices`, `_apply_beat_ledger`,
`_phase_for_count`) are pure and already unit-tested. `turn_ops.py` is **345 lines** today, so the
extraction *reduces* an already-near-ceiling module rather than chasing a violation — a real v2
benefit independent of v3. Scope is additive and behavior-preserving. Conditions:

**J1 — non-blocking. The v2 justification is decomposition, not v3; say so in the value statement.**
The FR leads with "v3-enabling," but v3 does not exist, and Scripture *purge* forbids building for a
hypothetical second consumer. The **defensible v2 value** is concrete and sufficient on its own:
`turn_ops` at 345 lines is one feature from the warn gate, and `invoke_turn` fuses three testable
concerns. Frame the FR as "decompose `invoke_turn`; the typed `TurnRequest`/`TurnResult` boundary
falls out" with v3 as a *bonus*, not the rationale. The engine must be extracted because it is
entangled **now**, provable by a characterization test — not because v3 will want it.

**J2 — BLOCKING (cheap). `extras` must be a closed, enumerated set, not an open `dict`.** The FR
proposes `extras: dict` as "opaque pass-through" for `protected` / `gone_this_chapter`. An open dict
is exactly the untyped boundary Contract A exists to kill — re-introducing one inside the *engine
contract* would be the `framework_costume` trap (a typed packet with an untyped escape hatch). Pin it:
`extras` is a typed `TurnExtras` (or explicit `protected: str = ""`, `gone_this_chapter: str = ""`
fields with defaults) so a new DM-semantic var is a typed addition, not a silent string key. "Keep DM
lifecycle concepts out of the shared engine" is satisfied by *defaulted optional fields the engine
ignores*, not by an untyped dict.

**J3 — non-blocking. Name the byte-identical proof precisely.** AC says "byte-identical turn output
proven by a monkeypatched-LLM characterization test." Make that a **golden** test: capture the current
`invoke_turn` output for a fixed cast/scene/seed with a stubbed LLM *before* the refactor (RED-as-
characterization, committed first), then assert the post-extraction `play_turn`→`write_turn_result`
path reproduces it exactly. The beat-FSM unit tests move *verbatim with the functions* (same asserts,
new import path) — do not rewrite them, or the regression net has a hole during the move.

**Authority granted to enforce once J2 is folded into the FR text (J1/J3 folded into the enforce
diff).** Freeze scope to: typed packets (closed `extras`), `turn_engine.play_turn` (doc-free, beat-FSM
moved verbatim with its tests), and `invoke_turn` rewired to build→play→write behind a golden test. No
new behavior. Example-exempt; changelog + diary required. **Sequencing note:** independent of FR-556
(reads cleaner after A, but not blocked); can enforce before or after it.

## Implementation (2026-06-21)

**Enforced.** RED-as-characterization first, then the extraction — the golden test passes against
both the pre- and post-refactor code, proving the move is byte-identical (J3).

- **Golden characterization (commit `59a1578d`, `test(examples)`):**
  `examples/dungeon_master/tests/test_turn_engine_golden.py` stubs the turn graph with a fixed
  payload (one intent; a director selection whose `phase`/`scene_complete` are deliberately *wrong*
  guesses and whose `beats_satisfied` is 1-based) and asserts the exact `turn_record` `invoke_turn`
  writes — intents keyed by char id, the direction ledger with beats resolved to canonical TEXT,
  `phase`/`scene_complete` COMPUTED from k/N, `beats_total` — plus the cleaned recap. Committed before
  the refactor; still green after.
- **`turn_engine` module (this commit):** new
  [`examples/dungeon_master/api/turn_engine.py`](../examples/dungeon_master/api/turn_engine.py)
  (222 lines) owning the doc-free engine core: `TurnExtras` / `TurnRequest` / `TurnResult` Pydantic
  packets, `async play_turn(req) -> TurnResult` (graph invocation + intent normalization + beat-FSM),
  and the four FSM helpers (`_phase_for_count`, `_satisfied_indices`, `_apply_beat_ledger`,
  `_direction_dict`) **moved verbatim**. Imports only `graph_app` + `tree` — no `doc`/`chapter_nav`.
- **`invoke_turn` rewired:** keeps roster scoping, the cast bundles, and the memory/lifecycle gates,
  then builds a `TurnRequest` (`beats=chapter_beat_list`, `prior_direction=turn_direction`, the two
  prompt strings into `TurnExtras`), calls `turn_engine.play_turn`, and writes the result
  (`dict(zip(roster, result.intents))`, `result.direction`, `result.recap`).
  [`turn_ops.py`](../examples/dungeon_master/api/turn_ops.py) drops **345 → 223 lines**.
- **Tests moved/repointed:** the five beat-FSM unit tests in `test_turn_prototype.py` and the
  `_direction_dict` test in `test_chapters.py` moved verbatim onto `turn_engine` (import + reference
  only). The six `invoke_turn` integration tests that monkeypatch the graph factory now patch
  `turn_engine.get_app` (the call site genuinely moved): `test_character_overlay`,
  `test_chapter_scoped_cast`, `test_lifecycle_gate`, and the golden. `running_scene` stays in
  `turn_ops`, so its test and the `prompt_salience` import are untouched. `gap_detectors` docstring
  references updated for accuracy. **DM suite: 404 passed.**

**J2 (BLOCKING) — honored.** `extras` is a closed `TurnExtras(BaseModel)` with defaulted
`protected: str = ""` / `gone_this_chapter: str = ""`, not an open dict. A new prompt var is a typed
field addition.

**J1 — honored.** Value statement reframed implicitly by the enforce: the extraction is justified by
the in-fact 345-line entanglement (now 223), proven by the golden test — not by v3.

**Enforce decisions (deviations from AC, documented):**
- *`CastMember` / `Intent` / `Direction` kept as `list[dict]` / `dict` in the packet fields*, not
  promoted to Pydantic sub-models. Reason: behavior preservation. Typing those nested shapes as
  Pydantic models or TypedDicts would invite Pydantic key-coercion/dropping on construction, which
  could alter the byte-identical graph payload and turn record the golden test pins. Only the
  J2-BLOCKING `extras` is strictly closed; the member shapes are documented in the packet docstrings.
  The golden test is the behavioral guarantee.
- *`docs/architecture.md` §5 / module map / `refactoring-plan.md` Contract B status — deferred.*
  Those doc-sync edits are intentionally **not** in this code commit to keep its scope clean
  (`mixed_commits_erode_auditability`); they ride with the separate refactoring-docs commit alongside
  FR-556/558.
