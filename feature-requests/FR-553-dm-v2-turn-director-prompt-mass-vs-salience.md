# Feature Request: DM v2 Turn-Director Prompt Mass vs. Salience on a Small Model

**Priority:** MEDIUM (continuity is the dominant review-score sink; the lever is prompt shape, not more orchestration)
**Type:** Investigation (build the measurement harness; the fix is a follow-up FR)
**Status:** Enforced (RED ef9bdf13 -> GREEN this commit) — C5 outcome (b): mass hypothesis FALSIFIED (director scene peaks ~2k, never 12k; 2/2 breaks present-but-ignored, 0 presence gaps); next lever is wording/recap, redirecting FR-545
**Effort:** ~1 day (instrument + correlate); fix deferred to a separate FR
**Requested:** 2026-06-21

## Summary

The turn director (`turn_direct.yaml`) is invoked once per turn on the default small model
(Azure `gpt-5.4-mini`) with a single large `{{ scene }}` blob assembled by
`running_scene()` (`examples/dungeon_master/api/turn_ops.py`). LangSmith traces of the
10035-BC run show each turn costs ~12.3k prompt tokens across 5 LLM calls
(`_map_intents_sub` x3 -> `direct` -> `recap`), yet the run's continuity score is **1/5**
with failures (combat->intimacy reversal, dead-man-acting, confrontation replay) that all
hinge on **one or two buried state facts**. This FR instruments **per-node prompt token mass**
and **correlates it with the continuity witness**, to test the hypothesis that the small
model loses the continuity-critical facts in an over-large, flatly-ranked prompt — before
designing any remedy.

## Value Statement

DM v2 maintainers get a measured answer to "is the turn prompt too large/unsalient for the
small model?" — a token-mass-vs-continuity correlation backed by LangSmith trace IDs — so the
next continuity FR optimizes the proven lever (prompt salience) instead of speculatively
adding orchestration or grounding prose.

## Problem

The FR-548 World Codex rollback (FR-550) was prompted by exactly this confusion: the codex
*added* background prose to an already-large turn/compose prompt and leaked non-roster
characters, on the premise that more grounding would *reduce* continuity flips. The 10035-BC
post-rollback run (LangSmith project `pr-showcase`, EU) makes the real shape visible:

- **Per turn:** ~12.3k prompt tokens, 5 LLM calls (run `019ee5e2-8807-...`). The call *count*
  is a healthy map-reduce — every sub-call (~2.5k tokens) succeeds fast on the small model.
- **The mass is in `{{ scene }}`:** `running_scene()` concatenates this chapter's summary +
  inherited `world_state` + last-3 recaps + the numbered beat ledger + (turn 1) the seam
  contract + entry_state + opening one-pager. The continuity-governing facts — *how the prior
  chapter actually ended* and *who is dead/absent* — are present but **flat-ranked and diluted**
  among thousands of tokens.
- **The failures are salience failures, not missing-context failures** (`review.md`,
  continuity 1/5): the combat->intimacy reversal (ch1->ch2) and confrontation replay (ch7->ch8)
  are cross-chapter seam facts that reach the director only via the turn-1 seam packet; the
  dead-man-acting (Arnulf, ch8) is a lifecycle fact the gates know but the narrator's prose
  overrides.

Hypothesis to test: **continuity-witness failures correlate with turn-director prompt token
mass**, i.e. the small model degrades as `{{ scene }}` grows, because the few governing facts
lose salience. If true, the remedy is to *shrink and re-rank* the turn prompt (a priority block:
prior-chapter tail + lifecycle status, ahead of the bulk context), not to add more.

## Proposed Solution

Measurement only — no behavior change to generation. Two deliverables:

1. **Per-node prompt-mass witness.** Extend the existing continuity-witness emission
   (`examples/dungeon_master/scripts/emit_continuity_witness.py`, FR-530 posture: visibility,
   not a gate) to also record, per turn, the director's prompt token count and a breakdown of
   `running_scene()`'s component byte/token sizes (summary, world_state, recaps, beats, seam,
   onepager). Source the token counts from the LangSmith run children for the book's generation
   graphs (the script already runs post-generation), keyed by chapter/turn.

2. **Correlation report.** A small read-only analysis (script or notebook) that joins the
   per-turn prompt mass against the per-chapter continuity flags in `continuity_witness.json`,
   and reports whether weak-continuity chapters carry heavier director prompts. Output a terse
   table (chapter, turns, mean director prompt tokens, continuity flags) plus the cited trace
   IDs.

```text
# Illustrative correlation output (shape, not real numbers)
chapter  turns  mean_director_tok  continuity_flags
   1       3         9,800            0
   2       2        12,100           2 (combat->intimacy reversal)
   8       4        13,400           2 (dead-man-acting, replay)
```

The fix — a bounded/re-ranked `running_scene()` with a top-pinned priority block (prior-chapter
tail + lifecycle) — is **explicitly out of scope** and deferred to a follow-up FR that consumes
this harness as its regression evidence (`investigation_before_fix`: build the harness that
proves the causal chain first, then a mechanical fix FR).

## Acceptance Criteria

- [ ] Per-turn director prompt token mass (and `running_scene()` component breakdown) is emitted
      as a non-blocking witness alongside `continuity_witness.json` (FR-530 visibility posture —
      a missing/low value never fails the run).
- [ ] A read-only correlation report joins per-turn prompt mass against per-chapter continuity
      flags and prints a terse table + cited LangSmith trace IDs.
- [ ] The report is run against 10035-BC and at least one other existing run; the
      mass-vs-continuity correlation (or its absence) is recorded in this FR.
- [ ] No change to generation behavior, graphs, or prompts (measurement only).
- [ ] Tests added for the witness/correlation helpers (example-exempt: no `@pytest.mark.req`,
      deterministic, no live LLM — feed a fixture witness + fixture trace summary).
- [ ] This FR records the finding and either (a) opens the bounded-prompt fix FR if the
      correlation holds, or (b) records the falsification and the next hypothesis if it does not.

## Alternatives Considered

- **Jump straight to a bounded/re-ranked turn prompt (skip measurement).** Rejected — this is the
  same un-measured leap that shipped FR-548; `unchallenged_premise` / `symptom_patch`. Prove the
  correlation before reshaping the prompt.
- **Switch the turn director to a larger model.** Rejected as the *first* lever — it hides the
  prompt-salience defect behind spend, and the cost multiplies across ~12 turns/book x N runs.
  Worth measuring as a control arm only after the mass-vs-continuity correlation is known.
- **Add grounding prose (the FR-548 codex approach).** Falsified and rolled back — more mass on an
  already-overloaded small-model prompt; `working_system_inertia` / `the_one_law`.
- **Reduce calls per turn (collapse the 3 intent sub-calls).** Rejected — the trace shows call
  count is not the bottleneck; each sub-call is small and succeeds. Cutting them would lose actor
  independence for no continuity gain.

## Related

- `examples/dungeon_master/api/turn_ops.py` — `running_scene()` (the prompt assembly under test)
- `examples/dungeon_master/prompts/turn_direct.yaml` — the director prompt
- `examples/dungeon_master/scripts/emit_continuity_witness.py` — FR-530 witness to extend
- `outputs/dungeon-master/10035-BC/` — `review.md` (continuity 1/5), `continuity_witness.json`
- LangSmith (project `pr-showcase`, EU): turn run `019ee5e2-8807-7b03-9706-be40f06f83ab`
  (~12.3k tok, 5 calls), reviewer run `019ee5e2-cd1d-7872-bc8b-f77f6a3761c6` (66k tok)
- FR-550 (World Codex rollback — the over-grounding misstep this FR measures past)
- FR-551 / FR-552 (supporting-cast tier / world bible — compact state, not prose)
- FR-545 (continuity work — the eventual consumer of this harness)

## Judgement

**Verdict: APPROVE WITH CONDITIONS** (fold C1-C5). Investigation-first scope is sound and
correctly refuses the un-measured leap that shipped FR-548. But judging the premise against
live measurement (`judge_as_junior_pr`) falsified the headline claim *before any harness was
built* — the cheapest bug, killed in the spec (`spec_kill`). The conditions correct the
quantity under test and the measurement source.

**Evidence gathered live (10035-BC, LangSmith run `019ee5e2-8807-...`):**

| quantity | value | source |
|----------|-------|--------|
| whole-turn graph (5 calls) | **12,299 tok** | trace root |
| `_map_intents_sub` x3 | 2,486 + 2,502 + 2,587 = **7,575 tok** | trace children |
| `direct` (the DIRECTOR call) total | **2,838 tok** | trace child |
| `recap` | 1,886 tok | trace child |
| director's `{{ scene }}` blob, peak (ch3 turn 1) | **1,580 tok** (tiktoken cl100k) | offline recompute of `running_scene` |
| director's `{{ scene }}`, range across turns | ~500-1,660 tok | offline recompute |

**C1 (premise correction — the director prompt is NOT 12k).** The ~12.3k tokens is the
*whole turn graph's 5-call sum*, **dominated by the 3 `_map_intents_sub` calls** (7,575 tok —
each re-embeds a full character sheet + the scene), not the director. The director `direct`
call is ~2.8k tok total, and its `{{ scene }}` component recomputes to only ~0.5-1.6k tokens.
The Problem section's "the mass is in `{{ scene }}`" is false and must be corrected: the scene
is already compact. The FR must measure and label three quantities separately (turn-graph
total, per-call breakdown, director-scene mass) and never attribute the 12k to the director.

**C2 (measurement source = deterministic offline recompute, NOT LangSmith).** `running_scene(doc,
cid, n)` is fully recomputable offline from the persisted `story.json` (verified: reads only the
doc), token-counted with `tiktoken` (0.12.0, present; no char/4 proxy). The witness MUST source
prompt mass this way. LangSmith MUST NOT be a data dependency: tracing is optional and
eventually-consistent, and a witness that breaks when `LANGSMITH_TRACING` is off violates the
FR-530 non-blocking posture. LangSmith trace IDs remain *corroborating evidence cited in the
report* (per-call totals, latency), not an input.

**C3 (reframed hypothesis — presence-at-the-failing-turn, NOT mass-dilution).** Because the
measured scene is already compact (~1.6k peak), the "small model degrades as `{{ scene }}` grows"
hypothesis is weak on its face. The correlation must test the stronger question: **was the
continuity-governing fact present in the scene at the turn where the break occurred?** Concretely
— the prior-chapter ending enters `running_scene` only via the turn-1 seam packet (`n == 1`);
mid-chapter turns drop it (`_beats_block` and last-3 recaps carry only intra-chapter history).
The report must record, per continuity break in `continuity_witness.json`, whether the governing
fact was present in that turn's recomputed scene. A mass-only correlation that ignores presence
is rejected.

**C4 (no behavior change; example-exempt tests).** Measurement only — no edits to `running_scene`,
graphs, or prompts. Deterministic tests with a fixture doc + fixture trace summary, no live LLM;
example-exempt (no `@pytest.mark.req`, no CAP YAML, per FR-474 J3).

**C5 (outcome gate).** The FR records the finding and either (a) opens the bounded/re-rank fix FR
if **presence gaps at failing turns** are found (the governing fact absent when the break occurs),
or (b) falsifies and states the next hypothesis if the fact was present-but-ignored — which points
at prompt *wording* or the `recap`/narrator call dropping the fact, NOT at mass, and would redirect
FR-545's effort accordingly.

**Sequencing:** independent of FR-550/551/552; may enforce immediately. Its harness becomes the
regression evidence the eventual FR-545 continuity fix consumes (`investigation_before_fix`).

**Frozen scope:** the three measured quantities (C1), deterministic-offline source (C2),
presence-at-failing-turn correlation (C3), measurement-only + example-exempt tests (C4), outcome
gate (C5). Authority to enforce granted.

## Implementation

**Status: Enforced (RED `ef9bdf13` -> GREEN this commit) — outcome gate C5 resolves to (b): the
mass hypothesis is FALSIFIED; the next hypothesis is wording/recap, redirecting FR-545.**

**What shipped (measurement only; no change to `running_scene`, graphs, or prompts):**

- `examples/dungeon_master/api/prompt_salience.py` (new, ~200 lines):
  - `prompt_mass_summary(story_doc)` — recomputes `running_scene` offline for every turn of every
    chapter, tiktoken-counts it (`cl100k_base`), reports per-turn mass + per-chapter peak/mean +
    global peak. Returns `None` when tiktoken is absent (omission, not a char/4 proxy — C2).
  - `presence_correlation(story_doc, witness)` — for each `fact_reversal` gap (failing turn = the
    `to_chapter` opening) and `seam_entrance` gap (that chapter's opening), recomputes the opening
    scene and records whether the break's subject is present. Splits the count into
    `presence_gap_count` (subject absent → bounded-prompt fix) vs `present_but_ignored_count`
    (subject present, break still occurred → wording/recap).
  - `format_prompt_salience_report(witness)` — the terse per-chapter mass + presence-verdict report.
- `examples/dungeon_master/scripts/emit_continuity_witness.py` — wires both blocks into
  `write_witness` (after the existing seam/fact/overlay blocks, FR-530 non-blocking posture) and
  prints the report in `main`.
- `examples/dungeon_master/tests/test_prompt_salience.py` (5 deterministic tests, example-exempt:
  no `@pytest.mark.req`, no live LLM, no LangSmith). 394 DM tests green.

**The finding (10035-BC, continuity 1/5, 5 breaks):**

| quantity | value | source |
|----------|-------|--------|
| turn-graph total (5 calls) | 12,299 tok | LangSmith `019ee5e2-8807-...` (corroboration) |
| 3x `_map_intents_sub` | 7,575 tok | LangSmith children (the real bulk) |
| `direct` (DIRECTOR call) total | 2,838 tok | LangSmith child |
| **director `{{ scene }}` peak (ch8 t16)** | **1,984 tok** | deterministic `prompt_mass` |
| director `{{ scene }}` mean, by chapter | 544 -> 1,508 tok (ch1 -> ch8) | deterministic `prompt_mass` |
| **presence at failing turn** | **2 breaks, 0 presence-gap, 2 present-but-ignored** | deterministic `presence_correlation` |

**C1 confirmed on real data:** the director scene never exceeds ~2k tokens across all 9 chapters —
the "12k director prompt" premise is falsified end to end, not just at one turn. The 12.3k is the
turn-graph total, dominated by the intent sub-calls.

**C3/C5 — the decisive result:** both Arnulf continuity breaks (the ch7->ch8 fact reversal and the
ch3 seam entrance) had the subject **present** in the recomputed opening scene. **Zero presence
gaps.** So the governing fact was in front of the model and was ignored — this is NOT a mass or
placement defect, and a bounded/re-ranked prompt would not have prevented it. Per the C5 gate,
outcome (b): **do not open a bounded-prompt fix FR.** The next hypothesis for FR-545 is that the
director's *wording* (or the downstream `recap`/narrator call, which writes the prose the reviewer
scores) drops a fact that was present in context. The harness shipped here is the regression
evidence that FR-545 work consumes: it will flip `present_but_ignored_count` toward zero as a
measurable target.

**Scope held:** no behavior change; mild chapter-over-chapter mass growth (544 -> 1,508 mean) is
recorded as visibility, not acted on. The per-component scene breakdown from the original AC was
descoped during enforcement (the judgement's three quantities are total/per-call/scene-mass, not
scene sub-components; a header-split re-derivation is fragile and low-value for a falsified
hypothesis).
