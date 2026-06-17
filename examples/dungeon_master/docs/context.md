# Dungeon Master v2 Context (Concurrent Sessions)

Purpose: shared starting context for running multiple coding sessions in parallel
without stepping on each other.

## Current State

- FR-503: enforced and witnessed (finite beat ledger; cap minority in witness run).
- FR-504: enforced (free-text beat fallback removed; non-empty beats contract).
- FR-505: re-judged and currently WITHHELD pending closure of:
  - C1: cue payload contract consistency.
  - C2: deterministic cue-uptake witness specification.

Primary active seam is Final Cut composition at chapter close.

## Scope Boundaries

In scope for FR-505 work:
- `examples/dungeon_master/api/turn_ops.py`
- `examples/dungeon_master/prompts/final_cut.yaml`
- `examples/dungeon_master/tests/` (new/updated unit tests)
- small deterministic metric helper under `scripts/` or example-local module
- `feature-requests/FR-505-final-cut-prose-degridding.md`

Out of scope unless explicitly re-planned:
- synopsis/characters/chapter planning phases
- per-turn participation policy from FR-486
- book-level revision passes

## Non-Negotiable Contracts

- Turns already store performance cards per character:
  `{name, thinking, intent, dialogue, expression}`.
- Current Final Cut input is recap/beats/climax only; no explicit cue payload.
- `beats_satisfied` is cumulative per turn.
- Beat grouping must be total and order-preserving; no orphaned turns.

## C1 and C2 Closure Targets

C1 (schema consistency):
- Choose one grouped card schema and keep it stable:
  `{name, intent, dialogue, expression}` with empty-string defaults.
- Do not delete required keys during payload trimming.

C2 (deterministic witness):
- Define exact cue-uptake proxy algorithm with normalization rules.
- Add unit tests with positive and negative fixtures.
- Record baseline and post-fix deltas in FR evidence.

## Recommended Parallel Session Split

Session A (Contracts + Tests)
- Implement/lock grouped payload schema.
- Write RED tests for beat grouping + cue-carrying invariants.
- Write RED tests for deterministic cue-uptake proxy.

Session B (Composition Seam)
- Implement `beat_turn_groups` and final-cut context re-key.
- Thread grouped `dialogue`/`expression` cues into Final Cut payload.

Session C (Prompt + Witness)
- Update `final_cut.yaml` for anti-round-robin and cue-use directives.
- Run witness generation + metric collection and update FR evidence.

## Safe Run Commands

Use explicit interpreter paths; do not assume shell PATH inheritance.

- Unit tests (example scope):
  `.venv/bin/python -m pytest examples/dungeon_master/tests/ --no-cov -q -p no:cacheprovider`

- Full example generation (logs streamed safely):
  `PYTHONPATH="$PWD" .venv/bin/python examples/dungeon_master/scripts/generate.py --premise "..." --out outputs/dungeon-master/<run-id> --turn-cap 96 2>&1 | tee logs/gen-<run-id>.log >/dev/null`

- If inspecting long command output, write to logs first and read logs separately.

## Coordination Rules

- Keep one concern per commit.
- Record FR updates in the same commit as the corresponding code/test state.
- If pre-commit modifies files, re-add and recommit with the same message file.
- Preserve unrelated working tree changes; do not revert out-of-scope edits.

## Handoff Note Template

Use this short block in session handoffs:

- Objective:
- Files touched:
- Tests run:
- Evidence gathered:
- Open blockers:
- Next smallest step:
