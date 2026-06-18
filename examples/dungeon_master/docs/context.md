# Dungeon Master v2 Context (Concurrent Sessions)

Purpose: shared starting context for running multiple coding sessions in parallel
without stepping on each other. The design doctrine is [`README.md`](../README.md);
the module map and seam split are in [`docs/architecture.md`](architecture.md).
This file is the **live status + working-agreement** layer on top of those.

## Current State (2026-06-18)

The example is a complete book pipeline (synopsis → cast → play every chapter →
deterministic Book). The active work seam is **continuity** — keeping a played
chapter's prose faithful to the physical/lifecycle state the recorded arc already
knows.

- **FR-513–518** — enforced. The forward-carry `world_state` is a typed,
  Pydantic-validated **ledger threaded as agent memory** (relationship deltas,
  bi-temporal reconciliation, top-K retrieval). The LLM authors meaning;
  deterministic code authors persistence.
- **FR-519** — enforced. **Intra-chapter prose-vs-state enforcement (Phase 1)** at
  the per-chapter Final Cut: confirmed-dead split into `dead_before_open` /
  `dead_within_chapter`, plus a `possession_facts` block. Warn-only diagnostics
  measure the residual.
- **FR-521** — enforced **via S2 roster-drop**. The director already flags an
  intra-chapter break every turn; **S1** (feed that advisory forward into the
  scene) was implemented, **witness-falsified** (Arnulf re-flags 8/16 → 13/16 — an
  instruction in the scene is not a gate), and **reverted**. **J2** stands:
  `missing_presumed_dead` is a chapter-scoped death-point in the warn-only lane.
  **S2** is the fix: a director-exited actor (structured `cast_exits`) is **dropped
  from the running cast** — Ch3 witness dropped Arnulf re-flags **8/16 → 0/16**
  (acting legitimately through his exit turn, then benched).
- **FR-522** — enforced. **Scripted single-chapter replay witness**: re-play one
  chapter from its inherited start (every prior chapter held constant) and compare
  director-flag vs intent-map acting counts against the recorded baseline. The
  instrument that drove FR-521's falsification and S2 acceptance.
- **FR-525** — enforced. **Outliner split-gate**: the whole-book partitioner
  (`outline_chapters` + `chapter_outline.yaml`) must not pack a death-AND-return
  reversal for one actor into a single capped chapter. A pure `reversal_pack_gap`
  detector re-rolls the outline (bounded) with the named violation, then RAISES.
  Kills the phantom-promise beat in the spec (`spec_kill`, `the_one_law`).
- **FR-526** — enforced. **Close-seam lifecycle coherence invariant**: a committed
  `CharacterLifecycle` row may never pair `confirmed_dead` with a non-null
  `allowed_reappearance_from_chapter`; the close softens it to
  `missing_presumed_dead`, preserving the allowance. Pure packet-only, applied after
  the index clamp.
- **FR-527** — **FALSIFIED at enforce → re-scoped to FR-528**. **Beat-progress early
  close**: the play loop closes a chapter only on `scene_complete` or the FR-501
  16-turn cap, never on `beats_satisfied`. A director that covers its playable beats
  then freezes rides the cap, replaying the resolved scene. Witness
  `scan_turn_waste.py` sized it at **208 wasted turns over 127 chapters (14/18
  books)**. The proposed `_beats_stalled` guard (close on a 3-turn beat-progress
  stall) was implemented under TDD and **falsified by its own J6 corpus safety
  check**: natural directors pause beat-marking mid-scene for up to **9 turns** then
  resume, so a count plateau is mid-scene noise, not a scene-end signal — no stall
  window both spares natural pauses and cuts the waste tail. Guard reverted; the cure
  is the OUTLINER refusing to author an un-satisfiable-in-scene final beat (FR-528).

The lesson threaded through this arc: **for a stochastic generator, enforcement is
removing the option (drop the actor from the cast), never discouraging the choice
(advisory text).** And: never measure a generator's output with a signal you have
injected into that same generator's input.

## Continuity Tooling (the witness layer)

- `scripts/replay_chapter_continuity.py` — single-chapter A/B replay (FR-522);
  driver in `api/chapter_replay.py`, pure metric in
  `witness_metrics.chapter_actor_flag_metrics`.
- `scripts/scan_beat_gaps.py` — phantom-promise reversal beats (FR-524 witness, the
  FR-525 condemning instrument): a chapter's own `world_state` contradicts a beat
  that promises a terminal actor's return.
- `scripts/scan_turn_waste.py` — no-progress-tail turn waste (FR-527 witness): for a
  force-capped chapter that never emitted `scene_complete`, the turns played after
  `beats_satisfied` last grew. (Honest signal is the STALL, not 100% beat coverage —
  the closing/resolution beat is never reported satisfied.)
- `scripts/witness_continuity_metrics.py` — FR-508 A5 book-level continuity counters
  from a generation log + `story.json`.
- `scripts/generate_and_review.sh` — full generation + `book_reviewer` critique.

These are **instruments, not gates** — efficacy is a non-deterministic, live-LLM
property and must never be wired into CI. Their *measurement* functions are
unit-tested; their *live runs* are by hand.

## Key Seams (where continuity is enforced)

- `api/turn_ops.py` — `running_scene` (turn context), `invoke_turn` (map → director
  → recap), `_filter_roster_for_lifecycle` + `cast_exits` (the S2 roster-drop),
  `dead_character_names` (the J2 within-chapter death-point),
  `reset_chapter_for_replay` (FR-522 replay surgery), Final Cut composition.
- `api/chapter_ops.py` — chapter close, the `world_state` ledger apply, the
  deterministic Book assembly.
- `prompts/turn_direct.yaml` — the director's per-turn `continuity` / `cast_exits`
  side-channel.

## Non-Negotiable Contracts

- Turns store performance cards per character:
  `{name, thinking, intent, dialogue, expression}`.
- `beats_satisfied` is cumulative per turn; `phase` / `scene_complete` are COMPUTED
  from k/N, not free-text.
- The shared card interface stays a pure `str → str`; structured side-channels live
  in `turn_ops.py` / `chapter_ops.py`, never in the interface.
- `world_state` is a typed ledger the model never regenerates whole; deterministic
  code authors persistence.
- Enforcement of a generator is **option removal** (roster drop, schema, computed
  rails), not advisory prompt text.

## Safe Run Commands

Use explicit interpreter paths; do not assume shell PATH inheritance.

- Unit tests (example scope):
  `.venv/bin/python -m pytest examples/dungeon_master/tests/ --no-cov -q -p no:cacheprovider`

- Full example generation (logs streamed safely):
  `PYTHONPATH="$PWD" .venv/bin/python examples/dungeon_master/scripts/generate.py --premise "..." --out outputs/dungeon-master/<run-id> --turn-cap 96 2>&1 | tee logs/gen-<run-id>.log >/dev/null`

- Single-chapter continuity replay (witness, live LLM):
  `PYTHONPATH="$PWD" .venv/bin/python examples/dungeon_master/scripts/replay_chapter_continuity.py --story outputs/dungeon-master/<run-id>/story.json --cid <n> --actor <Name> > logs/replay-<run-id>.log 2>/dev/null`

- If inspecting long command output, write to logs first and read logs separately
  (never pipe pytest to `head`/`tail` — `tee` to a logfile).

## Coordination Rules

- Keep one concern per commit.
- Record FR updates in the same commit as the corresponding code/test state — the
  FR is the source of truth for the change.
- TDD: commit RED (failing test) and GREEN (fix) separately.
- A `feat`/`fix` change needs a changelog fragment in `changelog/unreleased/` and a
  diary reflection in `docs/diary/` (the CI gates require both).
- Example tests are REQ-exempt (FR-474 J3 regime) — no `@pytest.mark.req`, no
  CAP/REQ minting, changelog fragment omits `req:`.
- If pre-commit modifies files, re-add and recommit with the same message file.
- Preserve unrelated working-tree changes; do not revert out-of-scope edits.

## Handoff Note Template

Use this short block in session handoffs:

- Objective:
- Files touched:
- Tests run:
- Evidence gathered (witness/replay deltas):
- Open blockers:
- Next smallest step:
