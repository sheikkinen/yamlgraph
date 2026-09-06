# Problem brief: the judge loop has no terminating condition below the human

**Prior art:** NC-414 (judge re-entry guard: prompt states it, `JUDGE_EXECUTION`
sentinel in `scripts/judge.sh` enforces it — the precedent for "doctrine in
`doctrine.md`, mechanism in the wrapper"); NC-412 (zero-duplication invariant:
`adapters/prompts/judge.yaml` is a thin pointer and may carry no doctrine);
FR-960 (per-backend-per-FR draft artifact path); FR-1013 (REJECTED by the
operator after four judgement rounds and three review rounds on a 20-line docs
sweep; superseded by FR-1019, ~40 lines); FR-746 (`ideal_result_backwards`);
`docs/diary/2026-09-06-reflection-fr-1013-rigor-as-surface-area.md` (names
`rigor_as_surface_area` and `own_churn_as_findings`; Seed asks for round
number and artifact growth to be printed beside the verdict).

## Problem statement

`scripts/judge.sh` will run the judge graph on the same FR any number of
times. Nothing in the wrapper, the graph, or `doctrine.md` reads the existing
`<fr>.judgement.md`, counts prior verdicts, or changes behaviour when a prior
verdict exists. The `APPROVED WITH REVISIONS` verdict says authority activates
"only after revisions are folded into the FR" but does not say who verifies
the fold — agents fill that gap with "run the judge again", and the judge, a
model, reads the now-longer FR and returns a new list of findings roughly
proportional to the text. Folding adds text; text invites findings. The loop
has no fixed point; it terminates only when the human says stop, and the
human is not put in the loop at any round.

Committed evidence on `main` (2026-09-06): seven `.judgement.md` files carry
two or more `**Verdict:**` lines; FR-1013's carries four. The hook audit log
shows `scripts/judge.sh` invoked 3–4 times on FR-948, FR-949, FR-890, FR-765
and FR-1001. In the FR-1013 case the FR grew from ~150 to 413 lines, the test
from 20 assertions to a 261-row sha256 baseline, a new REQ was minted, and
roughly half the later findings were defects introduced while folding the
previous round. The operator closed the PR unmerged and re-filed the same
edits as a ~40-line FR.

The judge is a good instrument for a first read. It is a bad instrument for
"is this plan still a plan" — that judgement is the human's, and the point at
which a planning document has stopped being a plan is a count, not a model
call.

## Classification

enforcement/latency-critical

## Constraints

- NC-412: no doctrine may live in `adapters/prompts/judge.yaml`; any rule
  must be stated in `.github/skills/judge-fr/doctrine.md` and enforced
  mechanically in `scripts/judge.sh`, following the NC-414 sentinel pattern.
- The mechanism must not be an LLM call: the whole failure is that the LLM
  produces a plausible verdict on every invocation. A deterministic count of
  prior verdicts in the committed `.judgement.md` is the only signal that
  cannot be talked around.
- No environment-variable override (`skip_env_as_bypass_by_another_name`,
  operator memory): a `JUDGE_FORCE=1` escape is `--no-verify` by another
  name. The legitimate exits already exist in doctrine — REJECT, or re-file as
  a new FR file (FR-1013 → FR-1019 is the witnessed correct exit).
- Legitimate re-judgement exists: a `SPLIT` or `REJECTED` FR re-enters as a
  NEW file and is round 1 of that file. The rule must key on the judgement
  file adjacent to the FR being judged, never on FR number or slug lineage.
- Round-2 fold verification is currently the only check that revisions were
  folded (the reviewer checks the PR, later); the rule must not remove the
  fold check without naming who does it.
- Verdict-line grammar is fixed: `grep -q '^\*\*Verdict:\*\*'` is already the
  wrapper's artifact contract (`scripts/judge.sh`); the same grammar counts
  rounds. Judgement files that were appended by hand ("# Round 2 …") already
  follow it (FR-1013).
- The wrapper's OS lock (`tmp/.judge.lock`), sentinel, backend validation and
  artifact contract are load-bearing (NC-415, FR-960) and must be untouched.
- `enforcement_at_merge_boundary` / `detection_without_enforcement`: a printed
  warning that does not block is advisory; FR-149 proved advisory
  insufficient.
- Enforcement-infrastructure change → adversarial input; human review is a
  GATE (doctrine.md "Judgement discipline").

## Witnessed incidents

- 2026-09-06, `feature-requests/FR-1013-chaplain-doctrine-sweep.judgement.md`:
  four `**Verdict:**` lines (AWR → SPLIT → AWR → AWR); FR `Status:`
  **REJECTED** by the operator, "the process around it became the
  deliverable"; superseded by FR-1019.
- 2026-09-06, `docs/diary/2026-09-06-reflection-fr-1013-rigor-as-surface-area.md`:
  "There is no fixed point inside the loop — it terminates only when a human
  says stop"; Seed: print round number and growth beside the verdict.
- 2026-09-06, `git log --since=2026-08-20 -- 'feature-requests/*.judgement.md'`:
  FR-1013 and FR-1001 judgement files committed 3× each; FR-936, FR-949,
  FR-950, FR-874, FR-849, FR-847, FR-1004, FR-1012, FR-1016 committed 2×.
- 2026-09-06, `.github/hooks/logs/audit.jsonl`: `scripts/judge.sh` invoked
  4× on FR-948, 3× each on FR-949, FR-890, FR-765, FR-1001.
- 2026-09-06, operator, this session: "several agent sessions have spiralled
  into endless judge-fr update cycles"; "third judgement is always following,
  no llm: 'Operator: Rethink and rewrite the FR. It's getting too complicated
  as a planning document.'"
