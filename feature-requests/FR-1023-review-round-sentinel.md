# Feature Request: Review round sentinel — the third review is not a model call

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed 2026-09-06 — research run in progress; unjudged. Stacked on FR-1022 (PR #633): depends on exit code 77, REQ-YG-668 under CAP-211, and the FR-1022 doctrine bullet.
**Effort:** 0.5 days
**Requested:** 2026-09-06
**First consumer / first event:** the next agent session that runs
`scripts/review.sh <pr> <fr>` on an FR whose adjacent `<fr>.review.md`
already records two review rounds. Today that run launches a third model
review and the review→judge ping-pong continues; after this FR it receives a
fixed verdict and stops. Second consumer: the reviewer in round 2, who for
the first time can read what round 1 said.
**Research:** [FR-1023.research.md](FR-1023.research.md) — brief
`feature-requests/research-briefs/review-round-sentinel.md`, run 2026-09-06,
4 of 5 personas executed (data_process failed schema validation on its own
`solution_class` field; its finding — same class — is recorded in the
failure line). All four converge on the class (wrapper-written per-FR
record, shell count before the model call) and split on the threshold
(3, 3, 1, unstated); the FR selects 2 and dispositions both variants under
Alternatives.
**Prior art:** [FR-1022-judge-round-sentinel.md](FR-1022-judge-round-sentinel.md)
— the judge half of the same loop; this FR is its review counterpart and
copies its shape (count → fixed text → exit 77 → no override). Differs in
one respect: the judge counts a record the agent promotes; the review has no
such record, so the wrapper writes it (see Problem).
[FR-960-claude-judge-variant.md](FR-960-claude-judge-variant.md) — gave the
judge a per-backend-per-FR draft path; the review draft path is still the
single clobbered `tmp/draft-review.md`. Parked, not in scope (Alternatives).
[FR-1004-retire-outsider-ledger.md](FR-1004-retire-outsider-ledger.md) —
retired a committed file that every PR appended to. The file this FR
introduces is per FR, mutated only by that FR's own PRs: the `.judgement.md`
class, not the ledger class. Distinguished, not contradicted.
[FR-865-ramp-installer.md](FR-865-ramp-installer.md) —
`.github/skills/review-pr/doctrine.md` is a byte-exact mirror of a ramp
asset; any doctrine edit here re-copies the mirror (PR #633 is failing CI
for omitting exactly this on the judge side).
[FR-1013-chaplain-doctrine-sweep.md](FR-1013-chaplain-doctrine-sweep.md) —
REJECTED; the witnessed incident (three review rounds, zero durable review
records), not a competing solution.

## Summary

`scripts/review.sh` gains two mechanical steps, both in the wrapper, none
in the graph or prompt:

1. **Record.** After a conforming draft passes the artifact contract, the
   wrapper appends the draft under a round heading to `<fr>.review.md`
   (adjacent to the FR, same lifecycle as `<fr>.judgement.md`). The human
   commits it with the fold, as they commit the judgement.
2. **Stop.** Before taking the lock, the wrapper counts round headings in
   that file. Zero or one: the graph runs (round 1, round 2; round number on
   stderr). Two or more: no model is launched, no lock is taken; the wrapper
   writes a fixed line to the draft path and exits 77:

   ```
   **Merge verdict:** Not approved — Operator: Two model reviews were not enough. The third read is the human's: merge on your own judgement, or close the PR and re-file the FR shorter.
   ```

   The sentence is provisional until the operator supplies their own
   (Questions for the human, Q-1). No flag or variable bypasses it.

Combined with FR-1022, one FR file can consume at most two judge rounds and
two review rounds of model time. FR-1013 consumed seven.

## Value Statement

Agent sessions stop ping-ponging between reviewer and judge: the third
review on any FR is the operator's sentence, every time, and round 2 can see
round 1 — so the only moves left are the human's, and they are made with the
record in front of them.

## Problem

The reviewer is a model; findings scale with text read; folding adds text.
FR-1022 states this for the judge and caps it. The review half is uncapped,
and worse: it has no record to count.

Raw record (main, 2026-09-06):

- `scripts/review.sh:12,46` — the draft path is the fixed `tmp/draft-review.md`,
  git-ignored, deleted with `rm -f` at the start of every run for any PR.
- FR-1013: reviews on PR #617 (7 findings), PR #627 (6), PR #627 (1). GitHub
  holds **0** review objects and **0** review comments on either PR; the
  three rounds survive only as "Review of PR #627 … folded" prose inside the
  FR. FR-1004's status line says "three review rounds enforced" — a phrase.
- `reference/command-book.md` entry 11 names "fix commits / disposition
  comments on the PR" as the durable record. The witnessed rounds produced
  neither in countable form.

A wrapper cannot count prose. So the sentinel needs a substrate before it
needs a threshold, and the substrate cannot depend on the agent choosing to
record — the agent in the loop is the one with the incentive to skip it.
That is why the wrapper writes the record here, where the judge leaves
promotion to the agent: the judge's record already existed by convention;
the review's never did.

## Ideal Result

A reviewer that runs at most twice per FR file, whose rounds leave a
committed, per-FR, human-readable trail the second round can read, and
whose third invocation is the operator's sentence delivered by the shell.
The merge decision was always the human's; after this FR the wrapper
returns it to them at a fixed, known moment. Nothing else in the review
route changes.

## Proposed Solution

### `scripts/review.sh` — exact order

1. usage / FR-existence (exit 64 / 66) — unchanged
2. `REVIEW_EXECUTION` re-entry guard (exit 70) — unchanged, still wins
3. `mkdir -p "$WORKDIR/tmp"`; round count — **new**
4. sentinel write and exit 77 when count ≥ 2 — **new**
5. lock (73 / 75), executor resolution (69), graph run — unchanged
6. artifact contract (65) — unchanged
7. append round record to `<fr>.review.md` — **new**; then exit 0

```bash
# FR-1023 round sentinel: two recorded review rounds on this FR file → the
# third review is fixed text, not a model call. No override exists.
RECORD="${FR_PATH%.md}.review.md"
ROUND=0
[ -f "$RECORD" ] && ROUND=$(grep -c '^## Review round [0-9][0-9]* — ' "$RECORD")
if [ "$ROUND" -ge 2 ]; then
  printf '%s\n' "**Merge verdict:** Not approved — Operator: Two model reviews were not enough. The third read is the human's: merge on your own judgement, or close the PR and re-file the FR shorter." > "$ARTIFACT"
  echo "review.sh: round $((ROUND + 1)) on $FR_PATH — sentinel verdict written: $ARTIFACT (no model run; human exits: merge on your own read, or close the PR and re-file a shorter FR)" >&2
  exit 77
fi
echo "review.sh: round $((ROUND + 1)) on $FR_PATH" >&2
```

After the artifact contract passes (step 7):

```bash
# FR-1023: the wrapper, not the agent, records the round (the review had no
# durable record before this; FR-1013 left three rounds as prose).
[ -f "$RECORD" ] || printf '# Review record: %s\n' "$(basename "$FR_PATH")" > "$RECORD"
{
  printf '\n## Review round %d — PR %s — %s\n\n' "$((ROUND + 1))" "$PR" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  cat "$ARTIFACT"
} >> "$RECORD"
echo "review.sh: round $((ROUND + 1)) recorded in $RECORD (commit it with the fold)" >&2
```

Decisions, with the alternative each rejects:

- **Count the wrapper's own heading grammar**, not `**Merge verdict:**`
  lines. The appended drafts are free text a reviewer writes; the headings
  are text the wrapper writes. Counting only what the wrapper wrote makes
  the count immune to a reviewer quoting the template mid-body.
- **Full draft appended, not line one.** Line one alone gives a count; the
  full draft gives round 2 its input and gives the FR the durable review
  record it never had. The cost is file length the human reads, which is
  the judgement file's cost too.
- **The sentinel round is not recorded.** No model ran; nothing to record;
  the file stays at two rounds and every later run returns the same exit.
- **Exit 77 reused from FR-1022** — same meaning in both wrappers: "sentinel
  verdict written, no model run". A caller distinguishing the two reads the
  script name in stderr.
- **Uncommitted record in a discarded worktree is lost.** Accepted: a round
  whose fold was never committed led nowhere; the next PR on that FR starts
  its own count from what was committed. The record travels with the fold.

### Doctrine and documentation

- `.github/skills/review-pr/doctrine.md` — one bullet at the end of "Review
  discipline", stating the record file, the two-round cap, the exact sentinel
  line, exit 77, the two human exits, and that the record is the durable
  review artifact. **Re-copy `ramp/assets/tier2/github/skills/review-pr/doctrine.md`
  in the same commit** (FR-865 mirror; AC-10).
- Input closure (same bullet): the reviewer MAY read `<fr>.review.md`; in
  round 2 it SHOULD, and should say which round-1 findings it re-checked.
- `.github/skills/review-pr/adapters/README.md` — one paragraph under the
  operator command: exit 77, the sentinel, the record file.
- `reference/command-book.md` entry 11 — durable column gains
  `feature-requests/FR-NNNN-<slug>.review.md`; the check column gains
  `grep -c '^## Review round' <fr>.review.md`.
- `adapters/graph.yaml` and `adapters/prompts/review.yaml` are not touched
  (NC-412; AC-10).

### Tests — `tests/unit/test_fr758_judge_review_wrappers.py`

Reuse `_run`, `_write_stub`, `fr_file`. New marker stub for the review side
(leaves `tmp/executor-ran`). Each test tagged `@pytest.mark.req("REQ-YG-669")`
(free on main and on the FR-1022 branch at filing — re-grep immediately
before allocation). REQ-YG-669 is added to
`capabilities/CAP-211-sole-route-judge-review.yaml` and `ARCHITECTURE.md`
regenerated. No new CAP.

## Acceptance Criteria

- [ ] AC-01: With no adjacent `.review.md`, the stubbed executor runs once,
      the wrapper exits 0, stderr contains `round 1`, and `<fr>.review.md`
      now exists with exactly one line matching `^## Review round 1 — PR 123 — `
      followed by the stub draft's text.
- [ ] AC-02: With one recorded round, the executor runs once, exit 0, stderr
      contains `round 2`, and the record holds two round headings, the
      first byte-identical to before.
- [ ] AC-03: With two recorded rounds, the wrapper exits 77; the executor
      marker is absent; the review lock is absent; `tmp/draft-review.md`
      consists exactly of the sentinel line plus one newline; and
      `<fr>.review.md` is byte-identical to before the run.
- [ ] AC-04: Two recorded rounds carrying different PR numbers (617, 627)
      produce the AC-03 result — the count is per FR file.
- [ ] AC-05: With two recorded rounds and `REVIEW_EXECUTION=1`, the re-entry
      contract wins: exit 70, no sentinel artifact, no marker, no lock, record
      unchanged.
- [ ] AC-06: Missing FR (66) and usage error (64) win over the sentinel with
      two recorded rounds: no artifact, no record write.
- [ ] AC-07: When the graph produces no artifact, or a draft whose line one is
      not `**Merge verdict:**`, the wrapper exits 65 as today and appends
      nothing to the record.
- [ ] AC-08: A line `**Merge verdict:** …` or `## Review round` text not
      matching the anchored heading grammar (indented, quoted, or inside a
      body) does not increment the round.
- [ ] AC-09: Setting an otherwise unused `REVIEW_FORCE=1` or passing an extra
      `--force` argument does not change the AC-03 result.
- [ ] AC-10: The doctrine bullet, adapter README, and command-book entry 11
      document the record file, exit 77, the exact sentinel, the two human
      exits, and advisory status;
      `tests/unit/test_ramp_installer.py::test_mirror_exact_entries_match_live_bytes`
      passes; `git diff --exit-code <base> -- .github/skills/review-pr/adapters/graph.yaml .github/skills/review-pr/adapters/prompts/review.yaml`
      succeeds.
- [ ] AC-11: New tests live in `tests/unit/test_fr758_judge_review_wrappers.py`,
      each tagged `REQ-YG-669`; the committed RED test precedes the GREEN
      implementation commit.
- [ ] AC-12: REQ-YG-669 appears under CAP-211 in both `ARCHITECTURE.md` and
      the CAP-211 yaml; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-13: `pytest tests/unit/test_fr758_judge_review_wrappers.py -q --no-cov`
      passes without invoking a real review graph.
- [ ] AC-14: Changelog fragment exists; the FR-1023 diary entry contains
      `**Seed:**`.

## Alternatives Considered

- **Count PR comments via `gh`** (command-book substrate) — rejected: needs
  network inside the wrapper; FR-1013's three rounds posted zero comments,
  so the count would have been 0; per-FR counting across PRs needs a search.
- **Agent-promoted `.review.md`** (exact judge parity) — rejected: the
  review record never existed by convention, and the agent in the loop is
  the party with the incentive to skip promotion. The wrapper writes; the
  human commits. Revisit if wrapper-written tracked files prove hostile in
  worktree flows.
- **Count in `.judgement.md`** — rejected: mixes two records; the judge
  sentinel would miscount.
- **Threshold 1 (block the second review)** (Subtractionist persona) —
  rejected for now: FR-1013's round 2 found six real items, half of them
  defects introduced by folding round 1; round 2 is the fold check. Parity
  with FR-1022's choice.
- **Threshold 3 (block the fourth review)** (os_infra and yamlgraph_native
  personas) — rejected: FR-1013's review 3 found one item and the operator
  closed the PR after it; a cap that permits the round the operator stopped
  at is not a cap. FR-1022 chose 2 for the judge on the same evidence.
- **Little-loops `.iter_counter` per artifact** (librarian) — same class as
  the selected design; confirms the count belongs in a per-artifact file
  read at the loop boundary, not in the loop body.
- **Per-PR draft path `tmp/draft-review-<pr>-<slug>.md`** (FR-960 analogue)
  — parked as its own FR; the record file removes the reason to keep drafts
  in `tmp/`, and the stub harness pins the current path.
- **Prompt-level refusal** — rejected: NC-412, and FR-1022's
  `prompt_as_mechanism` trap.
- **Override flag** — rejected: `--no-verify` by another name; the human
  exits already exist.

## Related

- `scripts/review.sh`, `.github/skills/review-pr/doctrine.md`,
  `.github/skills/review-pr/adapters/README.md`, `reference/command-book.md`
- `ramp/assets/tier2/github/skills/review-pr/doctrine.md` (mirror)
- `tests/unit/test_fr758_judge_review_wrappers.py`
- `docs/diary/2026-09-06-reflection-fr-1022-the-count-the-model-cannot-argue-with.md`
  (the Seed this FR answers)

## Judgement (pending)

Route: `scripts/judge.sh feature-requests/FR-1023-review-round-sentinel.md`
from this worktree, after the research record is promoted. Never in this
author session.

### Questions for the human (as options, or 'none')

1. **Q-1 The fixed sentence.** FR-1022's was the operator's own words. The
   line above is a placeholder in the operator's voice. Options: (a) keep
   as drafted; (b) operator supplies the sentence — *recommended*; the
   token stays `Not approved`.
2. **Q-2 Who writes the record.** (a) the wrapper appends `<fr>.review.md`
   after a conforming run — *recommended, as drafted*; (b) the agent
   promotes, judge parity, count depends on discipline.
3. **Q-3 Doctrine surface.** (a) one bullet in `review-pr/doctrine.md` plus
   ramp mirror re-copy — *recommended, "doctrine states, wrapper
   enforces"*; (b) adapter README only, no mirrored file touched.
