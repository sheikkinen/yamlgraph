# FR-479: DM v2 — Director/Narrator Split (Scene Start, End & Continuity Steering)

**Priority:** MEDIUM
**Type:** Enhancement (DM v2 prototype; inherits FR-474 J3/J4 regime)
**Status:** Implemented (2026-06-13). The original
plan proposed two Vane cures and a node rename; Judgement scoped the roster fix
out to its own FR, kept continuity detection informational, and rejected the
rename to preserve the `recap` contract. See *Judgement* and *Implementation Status*.
**Effort:** ~1 day (prototype)
**Requested:** 2026-06-13
**Judged:** 2026-06-13

**Continues:** FR-477 (the turn play-loop). Same J3 rules apply — **no CAP/REQ,
no CI gate, no demo-log**; the walkthrough tests under
`examples/dungeon_master/tests/` are a visibility harness, not a gate.

## Summary

Split the single per-turn `recap` node into two steps — a structured **director**
that judges the scene state and a prose **narrator** that writes the turn text —
so the play loop knows when a scene has *opened*, when it is *complete*, and can
*steer* the narration when character actions drift from the scene plan.

## Value Statement

The DM gets a scene that begins with an establishing description, ends when the
key scene's END state is reached (instead of replaying the climax indefinitely),
and self-corrects when a turn introduces a character or action the plan never
sanctioned.

## Problem

The per-turn graph is `intents (map) → recap (single llm)`. The `recap` node does
two jobs fused into one prose blob: it *judges* the scene state and it *writes*
the narration. Three failures follow, all observed in run `1732b9c4`
("10,000 B.C. in heat", 27 turns):

1. **No completion signal — the scene never ends.** The key scene's END (Torin
   dead; Kaelen mate + leader) is satisfied by ~turn 16, but the loop kept running
   to turn 27, recycling the resolution ("The New Leader" at T16 *and* T23;
   "The Shared Vessel" at T11 *and* T20; the mating ritual narrated three times).
   `running_scene` only carries the last 3 recaps and asks the model to "advance
   one step toward the END" — once the BEATS are exhausted there is nothing left
   to advance, so it loops. Nothing emits "the scene is complete."

2. **No opening beat.** Turn 1 jumps straight into action. The key scene plan
   already contains INT/EXT, LOCATION, TIME, and a START roster, but the recap
   never renders an establishing description; the scene has no curtain-up.

3. **No continuity steering — phantom actors.** **Vane** is named in **28/28**
   recaps yet is **not in the roster** (`[kaelen, mira, torin]`). He is listed in
   the key scene's CHARACTERS block, so the narrator animates him (accepts the
   tusk, pours the juice, submits to Kaelen) — but he has no intent step. He is a
   puppet the narrator moves at will, and there is no mechanism to notice that a
   non-roster name is taking decisive plot action.

These are all the same root cause: **decisions that live only as prose cannot be
branched on, gated on, or corrected.**

## Proposed Solution

Replace the single `recap` node with a **director → narrator** pair. The `intents`
map is unchanged.

```mermaid
flowchart LR
  START --> intents["intents (map over cast)"]
  intents --> direct["direct (structured judgment)"]
  direct --> narrate["narrate (turn prose)"]
  narrate --> END
```

### 1. `direct` — structured director (new node)

Inputs: the scene plan, the running history, this turn's intents, the roster.
Output schema:

| field | type | purpose |
|-------|------|---------|
| `phase` | str enum `opening`/`rising`/`climax`/`resolved` | where the arc stands |
| `establishing` | str | scene-setting description; non-empty only when `phase=opening` |
| `beats_satisfied` | list[str] | which key-scene BEATS are now done (evidence for completion) |
| `scene_complete` | bool | the END state has been reached |
| `steer` | str | guidance handed to the narrator (e.g. demote a phantom actor to scenery) |
| `continuity` | list[str] | flags: non-roster names taking decisive action, START/beat contradictions |

### 2. `narrate` — prose narrator (the old `recap`, render-only)

Receives the existing intents/scene plus the new `establishing` and `steer`. On
the opening turn it prepends the establishing description; every turn it applies
`steer` (e.g. "Vane is background scenery — no decisive action or dialogue") while
keeping the dry, factual key-scene voice. Render and judge stay in separate nodes
so structured judgment never contaminates the prose (avoids the
plausible-wrong-answer trap).

### 3. Consuming the signals (session / UI)

- **End:** when `scene_complete` is true, the play UI stops offering "Next turn"
  and offers **"Wrap scene"** (or auto-marks the turn stage reviewed). `direct`'s
  output is recorded alongside the turn's `intents` as a structured side-channel
  (J3 shape preserved — the `recap` entry stays `{text, reviewed}`).
- **Steer/continuity:** `steer` is auto-fed to `narrate`; `continuity` flags
  surface to the DM, who can Iterate with a correction.

### 4. The Vane case — resolved by Judgement (see J1–J2)

The roster-reconciliation cure (drafting Vane as a real player) is a
**character-phase** concern, not a turn-loop concern, and is **split out to its
own FR** (J1). FR-479 ships **continuity detection only**: `direct` flags any
non-roster name taking decisive action, and the flag is **surfaced to the DM,
not auto-applied as steer** — because Vane performs plot-critical acts the scene
plan requires (accepting the tusk, ending the bargain), so an automatic
"demote to scenery" steer would *starve* the scene (J2).

## Judgement (2026-06-13)

Verified against [turn_ops.py](../examples/dungeon_master/api/turn_ops.py)
(`invoke_turn` reads `result.get("recap")`/`result.get("intents")`, writes
`record["intents"]`, recap entry stays `{text, reviewed}`) and
[turn.yaml](../examples/dungeon_master/turn.yaml). Seven binding rulings, folded
into the solution above:

- **J1 — Roster reconciliation is out of scope.** Drafting Vane as a real player
  changes the *preplan/character* phase, raises its own questions (auto-draft vs
  offer; what when a scene names six characters), and is not required to deliver
  the three turn-loop signals. Split to a separate future FR. FR-479 ships
  continuity *detection* only.
- **J2 — Continuity is informational, not auto-steer.** A blanket "demote
  non-roster names to scenery" steer would break this very scene — Vane must
  accept the tusk and pour the juice for the plan to resolve. So `continuity`
  flags surface to the DM for a human call; they are NOT folded into `steer`.
  `steer` is reserved for **temporal/arc drift** (skip-ahead, replay of a past
  beat), which is safe to auto-apply to the narrator.
- **J3 — Preserve the `recap` output contract; reject the rename.** The original
  plan renamed the node `recap`→`narrate` and the file
  `turn_recap.yaml`→`turn_narrate.yaml`. Rejected: `invoke_turn` and the
  `{text, reviewed}` entry depend on the graph emitting `recap`. The existing
  node keeps its name and `state_key: recap`; only its *behaviour* changes
  (render-only, consumes `establishing` + `steer`). The new node is `direct`;
  the new prompt is `turn_direct.yaml`. Minimal blast radius.
- **J4 — Director output is a side-channel mirroring `intents`.** Add `direction`
  to the turn-graph state; `invoke_turn` records `turns[n].direction` alongside
  `turns[n].intents`. The recap entry shape is untouched (preserves FR-477 J3).
- **J5 — `scene_complete` consumption is minimal.** No multi-scene semantics. The
  play UI surfaces `scene_complete` (an indicator) and stops offering a plain
  "next turn" advance once true; "wrap" means "mark the scene resolved / stop
  advancing," nothing more. The over-specified "Wrap scene" button semantics are
  dropped.
- **J6 — `establishing` fires on the opening turn.** Opening = no prior history
  (`running_scene` already detects "Nothing has happened yet"). The director
  writes `establishing`; the render-only `recap` node prepends it that turn only.
- **J7 — Acceptance is structural markup + one live check (FR-474 J3).** The
  walkthrough harness asserts graph shape (`intents → direct → recap`), the
  director schema, the opening establishing description, and that
  `scene_complete` persists and is surfaced. Director *semantic quality* and
  *timing* are a manual live check.

## Acceptance Criteria (structural, per FR-474 J3)

- [ ] The turn graph runs `intents (map) → direct → recap`; the `intents` map is
      unchanged and the final node keeps `state_key: recap` (J3).
- [ ] `direct` emits at least `phase`, `establishing`, `scene_complete`, `steer`,
      and `continuity`; `invoke_turn` persists it as `turns[n].direction`, a
      side-channel alongside `intents`, without changing the `recap` entry's
      `{text, reviewed}` shape (J4).
- [ ] On the opening turn (no prior history), the rendered turn text includes an
      establishing description sourced from `establishing` (J6).
- [ ] When `direct` reports `scene_complete`, the play UI surfaces it and stops
      offering a plain "next turn" advance — no new multi-scene semantics (J5).
- [ ] A non-roster name taking decisive action produces a `continuity` flag that
      is surfaced to the DM; the flag is NOT auto-applied as `steer` (J2).
- [ ] `steer` carries temporal/arc-drift guidance and is auto-applied to the
      `recap` render; it does not carry phantom-actor demotion (J2).
- [ ] A walkthrough test drives a scene to its END and asserts `scene_complete`
      flips true and is surfaced; another asserts the opening turn carries an
      establishing description and that the graph shape is `intents → direct →
      recap`.
- [ ] Live manual check: a played scene opens with a description, ends at the END
      state without replaying the climax, and a phantom actor is flagged.

## Out of Scope

- **Roster reconciliation / drafting Vane as a real player** — split to its own
  future FR (J1); FR-479 ships continuity *detection* only.
- Multi-scene chaining / "what happens after this scene" (this FR ends ONE scene).
- Automatic turn execution (the loop stays human-driven, one turn per press).
- Auto-demoting phantom actors to scenery (J2 — would starve plan-critical roles).
- Streaming the director's reasoning to the UI.
- Re-planning the key scene mid-play.

## Alternatives Considered

- **Cheap heuristics only** (turn cap, repetition detector). Rejected: ends the
  loop but gives no opening beat and no continuity steering — addresses one of
  three problems.
- **Beat-checklist tracking** (parse BEATS, mark each done, end when all fire).
  Folded into `direct.beats_satisfied` as evidence rather than a separate brittle
  string-matching pass.
- **One fused node emitting both judgment and prose** (a richer schema on the
  current `recap`). Rejected: mixing structured judgment and prose in one schema
  is the plausible-wrong-answer trap; keeping judge and render apart is the point.

## Files (anticipated)

| File | Change |
|------|--------|
| `examples/dungeon_master/turn.yaml` | add `direct` node between `intents` and `recap`; add `direction` to state; new edges. The final node keeps `state_key: recap` (J3) |
| `examples/dungeon_master/prompts/turn_direct.yaml` (new) | structured director prompt + `output_schema` (`phase`, `establishing`, `beats_satisfied`, `scene_complete`, `steer`, `continuity`) |
| `examples/dungeon_master/prompts/turn_recap.yaml` | render-only; consume `establishing` + `steer` (kept name, J3) |
| `examples/dungeon_master/api/turn_ops.py` | capture `result["direction"]` into `turns[n].direction`; expose `scene_complete` / `continuity` (no change to the recap return contract) |
| `examples/dungeon_master/api/session.py` / templates | surface `scene_complete` (stop offering plain next-turn) and continuity flags |
| `examples/dungeon_master/tests/test_turn_prototype.py` | assert graph shape, director schema, completion signal, opening description, continuity flag |

*(Roster reconciliation / `tree.py` changes for drafting Vane are split out per
J1 and do not appear here.)*

## Implementation Status (2026-06-13)

Shipped exactly the frozen scope (J1–J7). All 22 DM walkthrough tests pass; the
new `direct` node lints clean; both prompts load and the recap Jinja renders the
director's `establishing` text through the passed-through `direction` dict.

| File | What shipped |
|------|--------------|
| `examples/dungeon_master/turn.yaml` | `direct` (llm, `parse_json`, `state_key: direction`) inserted between `intents` and `recap`; `direction: dict` added to state; edges `intents→direct→recap`. Final node keeps `state_key: recap` (J3). |
| `examples/dungeon_master/prompts/turn_direct.yaml` (new) | DIRECTOR system prompt + `output_schema` required `[phase, establishing, beats_satisfied, scene_complete, steer, continuity]`. `establishing` fires on opening only (J6); `steer` reserved for temporal/arc drift; `continuity` reports non-roster decisive actors without rewriting (J1/J2). |
| `examples/dungeon_master/prompts/turn_recap.yaml` | Consumes `direction.establishing` (opens the paragraph) and `direction.steer` (arc correction). Kept name + `recap` contract (J3/J4). |
| `examples/dungeon_master/api/turn_ops.py` | `invoke_turn` seeds `direction: {}`, records `turns[n].direction` via type-preserving `_direction_dict` (does NOT use `field`, which str-coerces and would corrupt `scene_complete`/lists); added `turn_direction(doc, n)` reader. Recap return contract unchanged. |
| `examples/dungeon_master/api/session.py` | `StageView` gains `scene_complete: bool` + `continuity: list[str]`; `_view` reads them from `turn_direction`; `_accept_target` returns `None` on `scene_complete` (stops plain advance, J5). |
| `examples/dungeon_master/api/templates/components/turn_card.html` | Surfaces `🏁 Scene complete` banner and `⚠ Continuity` flags (informational, never auto-applied). |
| `examples/dungeon_master/tests/test_turn_prototype.py` | 4 new tests: graph shape, opening establishing, scene-complete stops/surfaces, phantom (`Naru`) continuity flag. |

**Deviations:** none. Roster reconciliation (drafting a phantom as a real player)
remains split out per J1; this FR ships continuity **detection** only.
