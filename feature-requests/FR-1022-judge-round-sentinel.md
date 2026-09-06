# Feature Request: Judge round sentinel — the third judgement is not a model call

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-09-06
**First consumer / first event:** the next agent session that runs
`scripts/judge.sh` on an FR whose adjacent `.judgement.md` already holds two
`**Verdict:**` lines. Today that run launches a third model judgement and the
loop continues; after this FR it receives a fixed verdict and stops.
**Research:** [FR-1022.research.md](FR-1022.research.md) — brief
`feature-requests/research-briefs/judge-round-sentinel.md`, run 2026-09-06,
4 of 5 personas executed (data_process failed schema validation on its own
`solution_class` field; its finding — same guard, threshold ≥ 1 — is
recorded in the failure line and dispositioned under Alternatives).
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
**Verdict:** REWRITE — Operator: Rethink and rewrite the FR. It's getting too complicated as a planning document.
```

— and exits. No model is consulted. No environment variable, flag, or
backend selection bypasses it. The rule is stated once in
`.github/skills/judge-fr/doctrine.md` (local conventions) and enforced once
in the wrapper, exactly as NC-414's re-entry guard is.

## Value Statement

Agent sessions stop spiralling: the third judgement on any FR is the same
eleven words every time, so the only moves left are the human's — reject, or
re-file a shorter plan as a new FR.

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
(`docs/diary/2026-09-06-reflection-fr-1013-rigor-as-surface-area.md`). The
hook audit log shows `judge.sh` run 4× on FR-948 and 3× on FR-949, FR-890,
FR-765, FR-1001.

The failure is not that the third verdict is wrong. It is that a third verdict
from a model is *always plausible*, so it never ends the loop. The
termination condition must be something a model cannot argue with: a count.

## Ideal Result

A judge that can be run at most twice per FR file. The third invocation is
not a judgement of the FR's content; it is a judgement of the *process* —
that a plan needing a third round has stopped being a plan — and it is
delivered in the operator's voice, verbatim, by the wrapper. The agent's
next move is forced: hand the FR back to the human, or rewrite it short and
re-file. Nothing else in the judge route changes.

## Proposed Solution

### `scripts/judge.sh` (after the FR-exists check, before backend validation and the lock)

```bash
# FR-1022: round sentinel. Two prior verdicts on this FR file → the third
# judgement is fixed text, not a model call. No override exists.
JUDGEMENT="${FR_PATH%.md}.judgement.md"
ROUND=0
[ -f "$JUDGEMENT" ] && ROUND=$(grep -c '^\*\*Verdict:\*\*' "$JUDGEMENT")
if [ "$ROUND" -ge 2 ]; then
  mkdir -p "$WORKDIR/tmp"
  printf '%s\n' "**Verdict:** REWRITE — Operator: Rethink and rewrite the FR. It's getting too complicated as a planning document." > "$ARTIFACT"
  echo "judge.sh: round $((ROUND + 1)) on $FR_PATH — sentinel verdict written: $ARTIFACT (no model run; re-file a shorter FR as a new file or REJECT)" >&2
  exit 77
fi
echo "judge.sh: round $((ROUND + 1)) on $FR_PATH" >&2
```

`ARTIFACT` is computed before this block today (FR-960); the block moves
below it. The lock is not taken — nothing runs that needs serializing. Exit
77 is a new, distinct code in the wrapper's taxonomy (64 usage, 66 missing
FR, 65 artifact contract, 69 no executor, 70 re-entry, 73/75 lock): the
caller can distinguish "sentinel verdict" from "judge ran" without parsing
the artifact, and the artifact still exists for anyone who follows NC-414's
"verify by artifact" rule.

### `.github/skills/judge-fr/doctrine.md` (Local conventions — one bullet)

> Round sentinel (FR-1022): a judgement file holding two `**Verdict:**`
> lines closes the judge route for that FR file. The third and every later
> `scripts/judge.sh` run writes the fixed verdict `REWRITE — Operator:
> Rethink and rewrite the FR. It's getting too complicated as a planning
> document.` without a model call and grants no authority. Exits: the human
> rejects, or the plan is rewritten shorter and re-filed as a NEW FR file
> (round 1 of that file; FR-1013 → FR-1019 precedent). No override exists.

### `.github/skills/judge-fr/adapters/README.md` — one sentence under the
operator command noting exit 77 and the verdict text. `judge.yaml` is not
touched (NC-412).

### `tests/unit/test_fr1022_judge_round_sentinel.py`

Stubbed `YAMLGRAPH_BIN`, same harness as
`tests/unit/test_fr758_judge_review_wrappers.py`:

1. no `.judgement.md` → stub runs, stderr contains `round 1`
2. one verdict line → stub runs, stderr contains `round 2`
3. two verdict lines → exit 77; stub NOT invoked (stub writes a marker
   file; assert absent); artifact exists and its first line is the fixed
   verdict verbatim
4. four verdict lines (FR-1013 shape, `# Round N` headings between) → same
   as 3
5. two verdict lines + `JUDGE_BACKEND=claude` → exit 77 (sentinel precedes
   backend routing)
6. two verdict lines + `JUDGE_EXECUTION=1` → exit 70 (re-entry guard still
   first; sentinel does not reorder existing guards)
7. a `**Verdict:**` occurrence not at line start (quoted inside prose) is
   not counted — the grammar is the wrapper's existing anchored one

### Requirement / capability

`REQ-YG-668` (free on main; the id minted on FR-1013's closed branch never
reached main) in `ARCHITECTURE.md`; `capabilities/CAP-266-judge-round-sentinel.yaml`.
Confirm both ids are still free at enforce time (`grep`, `ls`) before
allocation — parallel sessions.

## Acceptance Criteria

- [ ] AC-1 `scripts/judge.sh` on an FR with 0 or 1 adjacent verdict lines
      runs the graph unchanged and prints `round 1` / `round 2` to stderr.
- [ ] AC-2 With ≥ 2 adjacent verdict lines: exit 77, graph executor never
      invoked, `tmp/draft-judgement-<backend>-<slug>.md` exists and line 1 is
      exactly `**Verdict:** REWRITE — Operator: Rethink and rewrite the FR.
      It's getting too complicated as a planning document.`
- [ ] AC-3 No environment variable or argument changes AC-2's outcome
      (witness: AC-2 holds with `JUDGE_BACKEND=claude`; `grep -c 'FORCE\|OVERRIDE'
      scripts/judge.sh` = 0).
- [ ] AC-4 `JUDGE_EXECUTION=1` still exits 70 before the sentinel evaluates.
- [ ] AC-5 Count uses the existing anchored grammar `^\*\*Verdict:\*\*`;
      unanchored occurrences do not count.
- [ ] AC-6 Doctrine bullet present in `.github/skills/judge-fr/doctrine.md`
      Local conventions; `adapters/prompts/judge.yaml` byte-identical to main
      (NC-412).
- [ ] AC-7 Tests 1–7 above in `tests/unit/test_fr1022_judge_round_sentinel.py`,
      tagged `REQ-YG-668`; RED commit precedes GREEN commit.
- [ ] AC-8 `python scripts/req_coverage.py --strict` passes; CAP-266 loads.
- [ ] AC-9 Changelog fragment `changelog/unreleased/fr-1022-judge-round-sentinel.md`.
- [ ] AC-10 Diary entry in `docs/diary/` with `**Seed:**`.
- [ ] AC-11 This FR's own judgement never reaches a third round. If it does,
      the sentinel is right and the FR is re-filed shorter.

## Alternatives Considered

- **Prompt-level refusal in `judge.yaml`** — rejected: NC-412 forbids
  doctrine in the pointer prompt, and a model told "refuse if judged before"
  is the same model that produces a plausible verdict on every call.
- **Threshold ≥ 1: block the second run unless the prior verdict was
  REJECTED/SPLIT** (data_process and Subtractionist personas) — rejected for
  now: round 2 is currently the only check that R-1..R-n were folded before
  implementation begins; removing it without naming a replacement verifier
  moves the fold check to PR review, after the code is written. Operator's
  stated threshold is the third round. Revisit if round-2 spirals recur.
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
