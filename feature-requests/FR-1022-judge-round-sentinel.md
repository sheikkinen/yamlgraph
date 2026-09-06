# Feature Request: Judge round sentinel — the third judgement is not a model call

**Priority:** HIGH
**Type:** Enhancement
**Status:** Completed 2026-09-06 — judged APPROVED WITH REVISIONS (1 round), R-1..R-5 folded, enforced (RED then GREEN), implementation record below
**Effort:** 0.5 days
**Requested:** 2026-09-06
**First consumer / first event:** the next agent session that runs
`scripts/judge.sh` on an FR whose adjacent `.judgement.md` already holds two
`**Verdict:**` lines. Today that run launches a third model judgement and the
loop continues; after this FR it receives a fixed verdict and stops.
**Research:** [FR-1022.research.md](FR-1022.research.md) — brief
`feature-requests/research-briefs/judge-round-sentinel.md`, two runs
2026-09-06 (second after R-4/review P2 corrected the brief): 5 of 5 personas,
convergent on the wrapper-side count, split on threshold (≥ 1 / ≥ 2 / ≥ 3);
the ≥ 1 variant is dispositioned under Alternatives.
**Prior art:** [NC-414 / scripts/judge.sh](../scripts/judge.sh) — the
`JUDGE_EXECUTION` lineage sentinel; this FR adds a second sentinel to the
same wrapper using the same pattern (doctrine states, wrapper enforces).
[FR-767-graph-authoring-sole-route.md](FR-767-graph-authoring-sole-route.md)
— PreToolUse sentinel for authoring writes; different surface (tool guard,
not wrapper), same doctrine-plus-mechanism shape.
[FR-886-judge-route-adoption-nudge.md](FR-886-judge-route-adoption-nudge.md)
— nudges sessions *into* the judge route when they judge by hand; this FR
bounds what the route does once inside. Complementary, no overlap.
[FR-980-id-ledger-route-enforcement.md](FR-980-id-ledger-route-enforcement.md)
— Superseded; vocabulary hit on "route enforcement", unrelated surface.
[FR-883-block-concealed-refusal-task-alteration.md](FR-883-block-concealed-refusal-task-alteration.md),
[FR-916-ban-dry-run-phrase.md](FR-916-ban-dry-run-phrase.md) — reasoning-pattern
sentinel registry hits on the noun "sentinel"; that registry inspects agent
reasoning text, this FR inspects a committed file. Dismissed.
[FR-1013-chaplain-doctrine-sweep.md](FR-1013-chaplain-doctrine-sweep.md) —
REJECTED; the witnessed incident, not a competing solution. Its exit
(re-file as [FR-1019](FR-1019-chaplain-doctrine-sweep.md)) is the exit this
FR's verdict text prescribes.
[FR-960-claude-judge-variant.md](FR-960-claude-judge-variant.md) — owns the
per-backend artifact path this FR writes to; unchanged.

## Summary

`scripts/judge.sh` counts `**Verdict:**` lines in the FR's adjacent
`.judgement.md` before taking the lock. Zero or one prior verdict: the judge
graph runs as today (round 1, round 2). Two or more: the wrapper does not
launch the graph. It writes a fixed, deterministic third verdict to the draft
artifact —

```
**Verdict:** REJECTED — Operator: Rethink and rewrite the FR. It's getting too complicated as a planning document.
```

— and exits 77. No model is consulted. No force/override input bypasses it
once the existing usage, FR-existence, backend-validation, and re-entry
checks have passed (R-2). The verdict token is `REJECTED` — one of the four
closed verdicts (R-1); the operator directive is its rationale. The draft is
advisory like every other: the human either marks the FR Rejected or re-files
a shorter plan. The rule is stated once in
`.github/skills/judge-fr/doctrine.md` (local conventions) and enforced once
in the wrapper, exactly as NC-414's re-entry guard is.

## Value Statement

Agent sessions stop spiralling: the third judgement on any FR is the same
fixed directive every time, so the only moves left are the human's — reject,
or re-file a shorter plan as a new FR.

## Problem

The judge is a model. It reads the whole FR and returns findings roughly
proportional to the text. `APPROVED WITH REVISIONS` requires the revisions to
be folded but names no verifier of the fold, so agents re-run the judge; the
fold made the FR longer; the longer FR yields a new list. The loop has no
fixed point below the human, and nothing puts the human in the loop at any
round.

Raw record (main, 2026-09-06): seven `.judgement.md` files carry ≥ 2 verdict
lines; FR-1013's carries four (AWR → SPLIT → AWR → AWR) interleaved with
three review rounds. A 20-line docs sweep became a 413-line FR and a 421-line
test before the operator closed the PR unmerged: "the process around it
became the deliverable". About half the later findings were defects
introduced while folding the previous round
(`docs/diary/2026-09-06-reflection-fr-1013-rigor-as-surface-area.md`).

(R-4: the untracked hook audit log's per-FR invocation counts are not
evidence; the committed judgement files and the diary are. The research brief
was corrected to drop them and the research route re-run — review P2.)

The failure is not that the third verdict is wrong. It is that a third verdict
from a model is *always plausible*, so it never ends the loop. The
termination condition must be something a model cannot argue with: a count.

## Ideal Result

A judge route that closes for an FR file once two verdicts have been
promoted into its adjacent judgement. The next invocation is not a judgement
of the FR's content; it is a judgement of the *process* — that a plan needing
a third round has stopped being a plan — and it is delivered in the operator's
voice, verbatim, by the wrapper. The agent's next move is forced: hand the FR
back to the human, or rewrite it short and re-file. The count is of
*promoted* verdicts: a draft that is never folded into `.judgement.md` does
not count, so this bounds recorded rounds, not raw model invocations (review
P3). Nothing else in the judge route changes.

## Proposed Solution

### `scripts/judge.sh` — exact order (R-2)

1. usage and FR-existence checks (exit 64 / 66) — unchanged
2. closed backend validation (exit 64) — unchanged
3. per-backend artifact derivation (FR-960) — unchanged
4. `JUDGE_EXECUTION` re-entry guard (exit 70) — unchanged, still wins
5. `mkdir -p "$WORKDIR/tmp"` and round count — **new**
6. round-sentinel artifact write and exit 77 when count ≥ 2 — **new**
7. lock acquisition and normal executor path — unchanged

```bash
# FR-1022: round sentinel. Two prior verdicts on this FR file → the third
# judgement is fixed text, not a model call. No override exists.
JUDGEMENT="${FR_PATH%.md}.judgement.md"
ROUND=0
[ -f "$JUDGEMENT" ] && ROUND=$(grep -c '^\*\*Verdict:\*\*' "$JUDGEMENT")
if [ "$ROUND" -ge 2 ]; then
  printf '%s\n' "**Verdict:** REJECTED — Operator: Rethink and rewrite the FR. It's getting too complicated as a planning document." > "$ARTIFACT"
  echo "judge.sh: round $((ROUND + 1)) on $FR_PATH — sentinel verdict written: $ARTIFACT (no model run; human exits: mark Rejected, or re-file a shorter FR as a new file)" >&2
  exit 77
fi
echo "judge.sh: round $((ROUND + 1)) on $FR_PATH" >&2
```

The lock is not taken on the sentinel path — nothing runs that needs
serializing. Exit 77 is a new, distinct code in the wrapper's taxonomy (64
usage/backend, 66 missing FR, 65 artifact contract, 69 no executor, 70
re-entry, 73/75 lock): the caller can distinguish "sentinel verdict" from
"judge ran" without parsing the artifact, and the artifact still exists for
anyone who follows NC-414's "verify by artifact" rule.

### `.github/skills/judge-fr/doctrine.md` (Local conventions — one bullet)

> Round sentinel (FR-1022): a judgement file holding two `**Verdict:**`
> lines closes the judge route for that FR file. The third and every later
> `scripts/judge.sh` run writes the fixed verdict `REJECTED — Operator:
> Rethink and rewrite the FR. It's getting too complicated as a planning
> document.` (exit 77) without a model call and grants no authority; it is
> advisory like every draft. Exits: the human marks the FR Rejected, or the
> plan is rewritten shorter and re-filed as a NEW FR file (round 1 of that
> file; FR-1013 → FR-1019 precedent). No override exists.

### `.github/skills/judge-fr/adapters/README.md` — one sentence under the
operator command noting exit 77, the exact `REJECTED` sentinel, the two
human exits, and advisory status. `graph.yaml` and `judge.yaml` are not
touched (NC-412; AC-10).

### Tests — in `tests/unit/test_fr758_judge_review_wrappers.py` (R-3)

Reuse its `_run`, stub, and FR fixtures; each new test tagged
`@pytest.mark.req("REQ-YG-668")`. The executor stub writes a marker file so
its absence proves no executor ran (C-7). Cases = AC-01..AC-09 below.

### Requirement / capability (R-3)

`REQ-YG-668` (free on main — the id minted on FR-1013's closed branch never
reached main; confirm by `grep` immediately before allocation, C-4) added to
`capabilities/CAP-211-sole-route-judge-review.yaml` and CAP-211's registry
row and requirement table in `ARCHITECTURE.md`. No new CAP: CAP-211 already
owns `scripts/judge.sh`, its sentinel and artifact contracts, and the FR-758
test file.

## Acceptance Criteria

Revised set per judgement R-5 (binding; replaces the originally filed
AC-1..AC-11):

- [x] AC-01: With no adjacent judgement, the stubbed executor runs once, the
      wrapper exits 0 with a conforming stub artifact, and stderr contains
      `round 1`.
- [x] AC-02: With exactly one anchored verdict line in the adjacent
      judgement, the stubbed executor runs once, the wrapper exits 0 with a
      conforming stub artifact, and stderr contains `round 2`.
- [x] AC-03: With exactly two anchored verdict lines and the default backend,
      the wrapper exits 77; the executor marker is absent; the judge lock is
      absent; and `tmp/draft-judgement-copilot-<fr-slug>.md` consists exactly
      of `**Verdict:** REJECTED — Operator: Rethink and rewrite the FR. It's
      getting too complicated as a planning document.` plus one newline.
- [x] AC-04: A four-verdict judgement with intervening `# Round N` headings
      produces the same exit, no-executor, no-lock, and exact-artifact result
      as AC-03.
- [x] AC-05: With two verdicts and `JUDGE_BACKEND=claude`, the wrapper exits
      77 and writes the exact sentinel to the Claude artifact; the executor
      marker is absent.
- [x] AC-06: With two verdicts and an invalid `JUDGE_BACKEND`, the existing
      backend contract wins: exit 64, no sentinel artifact, no executor
      marker, and no lock.
- [x] AC-07: With two verdicts, a valid backend, and `JUDGE_EXECUTION=1`, the
      existing re-entry contract wins: exit 70, no sentinel artifact, no
      executor marker, and no lock.
- [x] AC-08: A verdict token not beginning a line does not increment the
      round; counting uses exactly the existing anchored grammar
      `^\*\*Verdict:\*\*`.
- [x] AC-09: No new argument or environment-variable bypass is introduced;
      setting an otherwise unused `JUDGE_FORCE=1` or passing an extra
      `--force` argument does not change the AC-03 result.
- [x] AC-10: The Local conventions bullet and adapter README document exit
      77, the exact `REJECTED` sentinel, the two permitted human exits, and
      advisory status; `git diff --exit-code <base> --
      .github/skills/judge-fr/adapters/graph.yaml
      .github/skills/judge-fr/adapters/prompts/judge.yaml` succeeds.
- [x] AC-11: The new tests live in
      `tests/unit/test_fr758_judge_review_wrappers.py`, each carries
      `@pytest.mark.req("REQ-YG-668")`, and the committed RED test precedes
      the GREEN implementation commit.
- [x] AC-12: REQ-YG-668 appears under CAP-211 in both `ARCHITECTURE.md` and
      `capabilities/CAP-211-sole-route-judge-review.yaml`; no CAP-266 file
      exists; `python scripts/req_coverage.py --strict` passes; the
      capability registry loads.
- [x] AC-13: `pytest tests/unit/test_fr758_judge_review_wrappers.py -q
      --no-cov` passes without invoking a real judge graph.
- [x] AC-14: The changelog fragment exists, and the FR-1022 diary entry
      contains `**Seed:**`.

## Alternatives Considered

- **Prompt-level refusal in `judge.yaml`** — rejected: NC-412 forbids
  doctrine in the pointer prompt, and a model told "refuse if judged before"
  is the same model that produces a plausible verdict on every call.
- **A new verdict token (`REWRITE`)** — rejected by judgement R-1: the core
  taxonomy is closed (APPROVED / APPROVED WITH REVISIONS / REJECTED / SPLIT);
  the sentinel emits `REJECTED` with the operator directive as rationale.
- **Threshold ≥ 1: block the second run unless the prior verdict was
  REJECTED/SPLIT** (data_process — failed schema — and Subtractionist
  personas; the research record's "convergent x4" is on the solution CLASS,
  not the threshold — R-4) — rejected: the selected design permits one
  fold-verification rerun (round 2) and blocks the third invocation. Round 2
  is currently the only check that R-1..R-n were folded before
  implementation begins; removing it without naming a replacement verifier
  moves the fold check to PR review, after the code is written. Revisit if
  round-2 spirals recur.
- **Round-2 as delta-only fold verification** (judge reads prior R-list +
  FR diff, may not add findings) — parked as a separate FR; it changes the
  judge prompt and doctrine core, and this FR's value is realised without
  it.
- **Print round number and FR growth, advisory only** (diary Seed) —
  `detection_without_enforcement`; FR-149 precedent. The round number is
  printed here as a side effect of the count; growth-since-last-round is
  parked.
- **Human override flag** — rejected: `skip_env_as_bypass_by_another_name`.
  The human's override is to re-file or to reject; both already exist.
- **External precedent** (librarian): max-iteration counters in agent
  frameworks (n8n) — same shape, confirms the fix is a scalar guard outside
  the loop body, not a smarter loop body.

## Related

- `scripts/judge.sh`, `.github/skills/judge-fr/doctrine.md`,
  `.github/skills/judge-fr/adapters/README.md`
- `tests/unit/test_fr758_judge_review_wrappers.py` (harness precedent)
- `docs/diary/2026-09-06-reflection-fr-1013-rigor-as-surface-area.md`
- `feature-requests/FR-1013-chaplain-doctrine-sweep.judgement.md` (the
  four-verdict fixture shape)

## Judgement (2026-09-06, round 1)

**Verdict:** APPROVED WITH REVISIONS — full text in
[FR-1022-judge-round-sentinel.judgement.md](FR-1022-judge-round-sentinel.judgement.md)
(sole route, `scripts/judge.sh`, backend copilot).

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| R-1 | `REWRITE` is outside the closed verdict taxonomy | Folded: sentinel emits `REJECTED — Operator: …`; "eleven words" → "fixed directive" |
| R-2 | Sentinel must not precede backend validation / re-entry guard | Folded: exact 7-step order in Proposed Solution; AC-06/AC-07 witness precedence |
| R-3 | CAP-266 duplicates CAP-211; tests belong in the FR-758 harness | Folded: REQ-YG-668 under CAP-211; tests in `test_fr758_judge_review_wrappers.py` |
| R-4 | Untracked audit-log counts cited as committed evidence; research header overstated convergence | Folded: dropped from FR; brief corrected and research route re-run (second record promoted, 5/5 personas) — review P2 |
| R-5 | AC set replaced with AC-01..AC-14 | Folded verbatim |

**Purge list:** CAP-266; `tests/unit/test_fr1022_*.py`; the `REWRITE` token;
`grep FORCE|OVERRIDE` proxy AC; self-referential AC-11.

**Scope frozen:** D-1..D-8 as listed in the judgement. Not authorized: edits
to `adapters/graph.yaml` or `adapters/prompts/judge.yaml`; changes to
`scripts/review.sh`; any override input; growth metrics; delta-only fold
verification; rewriting historical judgement files; automatic status
changes, commits, or re-filing.

### Questions for the human (as options, or 'none')

1. **Verdict token for the sentinel line.** Judge's R-1 says `REJECTED`
   (closed taxonomy). Operator's original wording had no token. Options:
   (a) `REJECTED — Operator: …` as folded — *recommended, default*;
   (b) reopen the taxonomy for a fifth token — not authorized by this
   judgement; would need its own FR.
2. **C-6 human review of this folded FR is the GATE** before enforcement
   begins. `merge`-book verdict word suffices.

Operator answer (2026-09-06): "enforce. pr. outsider. review. merge" —
(a) accepted by default; C-6 cleared by the enforce verdict.

## Implementation record (2026-09-06)

| Step | Witness |
|---|---|
| RED | commit `test(judge): FR-1022 RED …` — 9 REQ-YG-668 tests appended to `tests/unit/test_fr758_judge_review_wrappers.py` (marker stub, C-7); 7 failing, 2 precedence tests (AC-06/07) green before and after by design; CAP-211 gains REQ-YG-668; `ARCHITECTURE.md` regenerated via `scripts/aggregate_capabilities.py`; `req_coverage.py --strict` green |
| GREEN | commit `feat(judge): FR-1022 round sentinel …` — 12-line block in `scripts/judge.sh` between `mkdir -p "$WORKDIR/tmp"` and the lock (step 5–6 of the R-2 order); doctrine bullet; adapter README note; changelog fragment. `pytest tests/unit/test_fr758_judge_review_wrappers.py -q --no-cov` → 27 passed |
| Ramp mirror | `ramp/assets/tier2/github/skills/judge-fr/doctrine.md` re-copied byte-exact from the live doctrine (`test_mirror_exact_entries_match_live_bytes`, REQ-YG-613) — review P1 |
| NC-412 | `graph.yaml` and `prompts/judge.yaml` untouched (AC-10) |
| Distill | `docs/diary/2026-09-06-reflection-fr-1022-the-count-the-model-cannot-argue-with.md` |

Decisions: no CAP-266 (R-3); no growth metric (parked). Review #633 round 1
(P1 ramp mirror re-copied; P2 brief corrected + research re-run; P3 claims
narrowed to promoted verdicts — the sentinel bounds recorded rounds, not raw
invocations). AC-01..AC-14 satisfied; AC-11's RED-before-GREEN is in `git log`.
