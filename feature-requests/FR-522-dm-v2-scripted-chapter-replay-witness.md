# Feature Request: FR-522 — DM v2: Scripted Single-Chapter Replay Witness

**Priority:** MEDIUM
**Type:** Feature (witness tooling)
**Status:** **Enforced (2026-06-18)** — built per the frozen Judgement: `turn_ops.reset_chapter_for_replay` (J1), the mockable async driver `api/chapter_replay.py` (J2), the pure metric `witness_metrics.chapter_actor_flag_metrics` reporting director-flag + intent-map acting counts (J3/J4), the thin CLI `scripts/replay_chapter_continuity.py`, and the `architecture.md` §5 note. 9 new unit tests (mocked-LLM isolation proven); full DM suite green, ruff + lint-imports clean; live smoke-run against 10022-BC Ch3. REQ-exempt (J5); not wired into CI (J6). It is the witness that drove FR-521's S1 falsification and S2 acceptance.
**Effort:** ~0.5 day
**Requested:** 2026-06-18

## Summary

A reusable, scripted harness that re-plays **one chapter** of an existing finished
story from its inherited start, holding every prior chapter constant, so a
continuity change can be measured against the recorded baseline as a controlled
experiment — one changed variable, same inherited state. Extracted and hardened
from the throwaway script written to falsify FR-521's S1
(`scripts/replay_chapter_continuity.py`).

## Value Statement

A DM developer can answer "did this continuity change actually reduce the break, on
the chapter that exhibited it?" in one command — turning the FR witness clause from
a manual, ad-hoc re-generation of a whole book into a fast, isolated A/B on the
single offending chapter.

## Problem

FR-521 shipped unit tests that proved its feed-forward **wiring** but could not
prove its **efficacy** — efficacy is a live-LLM property. The witness was deferred
as "corroboration, not a gate." When finally run, the witness **falsified the
design** (Arnulf re-flags rose 8/16 → 13/16), but only because a one-off script was
hand-built to do it. That capability should not be a disposable script:

- Re-generating a full book to test a single-chapter fix is slow (8 chapters × ~16
  turns) and confounded — every chapter's LLM roll differs, so the signal is buried
  in run-to-run noise across the whole book.
- A controlled single-chapter replay **holds the inherited state constant** (the
  real independent-variable isolation), so the only thing that changed is the code
  under test. That is the difference between an experiment and an anecdote.
- The "which chapter offended, and by how much" measurement (per-turn actor flag
  count vs baseline) is itself reusable across every future continuity FR
  (FR-519 → FR-521 → the pending S2 roster-drop), not Arnulf-specific.

This is the Scripture's `demo_vs_test` / Commandment 2 made operational: tests prove
constraints, **the witness proves the abstraction is worth having** — and FR-521
proved a witness can also prove an abstraction is *not* worth having, before it is
trusted.

## Proposed Solution

Promote `examples/dungeon_master/scripts/replay_chapter_continuity.py` to a
first-class, tested witness with the measurement logic moved into the testable API
layer (the script stays a thin CLI, mirroring `witness_continuity_metrics.py`).

```bash
PYTHONPATH="$PWD" .venv/bin/python \
  examples/dungeon_master/scripts/replay_chapter_continuity.py \
  --story outputs/dungeon-master/10022-BC/story.json \
  --cid 3 --actor Arnulf \
  --out outputs/dungeon-master/10022-BC/ch3-replay.json
```

```
BASELINE  ch3: 8/16 turns flagged Arnulf (recorded run, no feed-forward)
REPLAY    ch3 with current code active:
  turn  4: 1 flag(s)  ⚑ Arnulf: Arnulf is acting despite having been swept away …
  …
RESULT    ch3: 13/16 turns flagged Arnulf (replay) vs 8/16 baseline
```

Design constraints (carried from the throwaway, hardened):

1. **Isolation by construction.** Deep-copy the doc; wipe ONLY the target chapter's
   `turns` + `reviewed` + its own committed `world_state`/`seam_packet`; re-play via
   the same `turn_ops.invoke_turn` the live loop uses (no doc-shape coupling of its
   own — mirrors `generate.py`'s "drive the real methods" rule). The inherited start
   (all prior chapters) is **never** mutated.
2. **Measurement in the API layer (testable).** Move `_actor_flag_turns` and the
   baseline/after comparison into `examples/dungeon_master/api/witness_metrics.py`
   (or a sibling) so it is unit-tested against a fixture doc, not only exercised by
   a live run. The script becomes argparse + print, like
   `witness_continuity_metrics.py`.
3. **Actor-agnostic.** `--actor` is a substring match on the director `continuity`
   strings; the metric is "turns flagging this actor / turns played," reusable for
   any character, any chapter, any continuity FR.
4. **Honest about the confound.** The replay carries a documented caveat that
   `running_scene` feeds the same `scene` to map → direct → recap, so a change that
   injects text into `scene` also reaches the director it measures (the FR-521
   metric-pollution lesson). The harness reports the **intent-map** acting count
   alongside the **director-flag** count, so a reader can separate "the actor really
   acted" from "the director echoed an injected warning."

## Acceptance Criteria

- [x] `replay_chapter_continuity.py` re-plays a single chapter from inherited start,
      mutating only the target chapter; a unit test asserts a prior chapter's
      `turns`/`world_state` are byte-identical after a (mocked-LLM) replay.
      (`test_replay_chapter_isolates_prior_chapters`,
      `test_reset_chapter_for_replay_wipes_only_target_chapter`)
- [x] The flag-count + baseline-vs-after comparison lives in the API layer and has a
      unit test against a fixture doc (deterministic; no live LLM): a doc whose
      chapter has N turns with K actor flags reports `K/N`.
      (`witness_metrics.chapter_actor_flag_metrics`;
      `test_chapter_actor_flag_metrics_reports_k_over_n_and_both_counts`)
- [x] The harness reports **both** the director-flag count and the intent-map acting
      count per turn (the confound separation), proven by a fixture test.
      (`render_report`; `test_render_report_shows_baseline_and_replay_counts`, and
      the per-turn `acting`/`flagged` fixture asserts)
- [x] `--actor` is honored as a case-insensitive substring; absent actor → `0/N`,
      no crash. (`test_chapter_actor_flag_metrics_actor_match_is_case_insensitive_substring`,
      `test_chapter_actor_flag_metrics_absent_actor_is_zero_not_crash`)
- [x] `--out` writes the replayed doc; omitted → no file written, summary still
      printed. (`maybe_write_doc`; `test_maybe_write_doc_writes_only_when_path_given`)
- [x] Tests added; the DM `architecture.md` notes the replay harness as the
      single-chapter witness primitive. (§5 "Single-chapter replay" subsection)

## Implementation (2026-06-18)

- **J1** `turn_ops.reset_chapter_for_replay(doc, cid)` — the one named, tested site
  for the chapter-wipe doc surgery (clears `turns`/`reviewed`, pops committed
  `world_state`/`seam_packet`); touches only the target card.
- **J2/J3** `api/chapter_replay.py` — the impure async driver `replay_chapter`
  deep-copies the doc (caller's never mutated) and drives the real
  `turn_ops.invoke_turn` loop until `chapter_should_close`; mockable, so
  `test_replay_chapter_isolates_prior_chapters` proves byte-identical prior
  chapters with a stubbed LLM. `render_report` + `maybe_write_doc` round out the
  thin-CLI surface.
- **J3/J4** `witness_metrics.chapter_actor_flag_metrics` (pure) — one
  continuity-flag extractor reused for baseline + replay; reports `flag_turns`
  (director) beside `acting_turns` (intent-map, J4: non-empty `intent` OR
  `dialogue` under an actor-matching key).
- **CLI** `scripts/replay_chapter_continuity.py` rewritten from the FR-521
  throwaway into argparse + `asyncio.run` over the API layer.
- 9 new tests; DM suite 213 passed; ruff + lint-imports clean; live smoke-run
  against 10022-BC Ch3 confirmed the report renders.

## Judgement (2026-06-18)

**Verdict: Granted with amendments. Scope frozen.** The pain is real and confirmed,
not speculative: this harness already falsified FR-521's S1 (8/16 → 13/16) in one
controlled run, and the pending S2 roster-drop names it as its acceptance witness —
two concrete consumers plus a reusable pattern clears CLAUDE.md's "documenting beats
building" bar. The FR is sound; these amendments resolve one contradiction and pin
three seams so the enforcer cannot drift.

- **J1 — The wipe IS doc-shape surgery; stop claiming otherwise.** Constraint 1
  asserts the replay has "no doc-shape coupling of its own," but wiping a chapter
  (`card["turns"] = []`, popping `world_state`/`seam_packet`, indexing
  `doc["chapters"]["cards"][cid]`) is unavoidably doc-shape surgery — only the
  *play* is driven through `invoke_turn`. Resolve the contradiction: extract the
  wipe into **one named, tested helper** `reset_chapter_for_replay(doc, cid)` (in
  `turn_ops.py`, beside `turn_record`), not scattered statements in the script. The
  "drive the real methods" rule applies to the *play loop* (`invoke_turn`), not to
  pretending the reset is coupling-free.

- **J2 — The replay driver must be importable and mockable, or AC-1 is unmeetable.**
  AC-1 demands "a unit test asserts a prior chapter is byte-identical after a
  *mocked-LLM* replay." That is impossible if the deep-copy → wipe → loop lives in
  the `__main__` script. The **driver** (the function that deep-copies, calls
  `reset_chapter_for_replay`, then loops `invoke_turn` until `chapter_should_close`)
  must be an `async` API-layer function taking the doc as an argument, so a test can
  monkeypatch `turn_ops.invoke_turn` with a stub. The script becomes argparse +
  `asyncio.run(driver(...))` + print — nothing else.

- **J3 — Pin the module split (pure vs impure); do not co-locate.** The FR's
  "`witness_metrics.py` (or a sibling)" is ambiguous. `witness_metrics.py` is a
  family of **pure** log/doc parsers (`parse_story_progress_metrics`, renderers) —
  the per-turn actor-flag/acting **measurement** belongs there (e.g.
  `chapter_actor_flag_metrics(doc, cid, actor) -> {flag_turns, acting_turns, total}`)
  and is unit-tested against a fixture doc. The **impure driver** (it awaits LLM
  calls) must NOT live in `witness_metrics.py`; put it in a new
  `examples/dungeon_master/api/chapter_replay.py`. Pure metric and impure driver do
  not share a module. The single per-turn continuity-flag extraction must be ONE
  function reused by both baseline and after-measurement (no `false_duplicate`).

- **J4 — Define "acting" so AC-3 is deterministic.** "Intent-map acting count" =
  the target actor appears in `turns[k].intents` with a non-empty `intent` OR a
  non-empty `dialogue`. Bind it to that definition in the metric function and the
  fixture test, so the confound-separation count is reproducible and not eyeballed.

- **J5 — REQ-exempt; create no CAP/REQ.** This is example-scoped witness tooling.
  Per FR-474 J3, example tests carry no `@pytest.mark.req`. Do not mint a
  `REQ-YG-XXX` or a `capabilities/CAP-XXX` for it; the changelog fragment omits
  `req:`. State this so `req_coverage.py` / the changelog-req gate are not fed a
  phantom.

- **J6 — Witness-only; forbid CI wiring.** The whole premise (mirrored from FR-521
  J5) is that efficacy is a non-deterministic, live-LLM property — it cannot be a
  pass/fail gate. The driver and metric are an **instrument**, not a gate: do not
  add it to a pre-commit hook, a workflow, or branch protection. Its *measurement
  functions* are unit-tested (deterministic); its *live replay* is run by hand.
  Wiring it into CI would manufacture exactly the flaky gate the FR was written to
  avoid (`detection_without_enforcement`'s inverse — a gate that cannot mean what it
  claims).

**Frozen scope.** Build: `reset_chapter_for_replay` (turn_ops), the async driver
(`chapter_replay.py`), the pure metric (`witness_metrics.py`), the thin CLI script,
the six ACs' tests, the architecture.md note. **Do not** add: a multi-chapter replay
mode, a config/flag surface beyond `--story/--cid/--actor/--out`, a stored
baseline-history format, or any CI integration. If a witness survives, the S2
roster-drop FR consumes this harness — it does not extend it.

## Alternatives Considered

- **Re-generate the whole book per change (status quo before FR-521's script).**
  Rejected — slow and confounded; the signal for a one-chapter fix is buried in
  seven other chapters' independent LLM rolls. No controlled comparison.
- **A pytest live-integration test that replays a chapter.** Rejected as the primary
  form — efficacy is non-deterministic (LLM), so it cannot be a passing/failing gate
  (the FR-521 J5 reasoning); it belongs as an opt-in witness script whose
  *measurement* is unit-tested, not whose *outcome* is asserted.
- **Keep it a throwaway script.** Rejected — every continuity FR (519, 521, the
  pending S2) needs exactly this controlled single-chapter A/B; a disposable script
  re-invents the isolation logic (and its subtle "don't mutate inherited state" bug
  surface) each time.

## Related

- `examples/dungeon_master/scripts/replay_chapter_continuity.py` — the throwaway
  origin (built under FR-521 to falsify S1; this FR hardens + tests it).
- `feature-requests/FR-521-*` — the witness that proved the harness's worth by
  falsifying its own S1 (8/16 → 13/16); the pending S2 roster-drop will use this
  harness as its acceptance witness.
- `feature-requests/FR-519-*`, `FR-505-witness-continuity-metrics` — prior
  continuity-measurement tooling this composes with.
- `examples/dungeon_master/scripts/witness_continuity_metrics.py` — the thin-CLI /
  API-layer-measurement pattern this should mirror.
- `examples/dungeon_master/api/turn_ops.py` — `invoke_turn`, `chapter_turns`,
  `turn_direction`, `chapter_should_close`, `CHAPTER_TURN_CAP` (the replay loop's
  building blocks).
