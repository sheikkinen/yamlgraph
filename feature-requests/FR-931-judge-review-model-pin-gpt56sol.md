# Feature Request: Upgrade the judge and review sole-route model pin to gpt-5.6-sol

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-30
**First consumer / first event:** the next FR judged after merge —
`scripts/judge.sh <fr>` renders its verdict on `gpt-5.6-sol` instead of
`gpt-5.5`; second consumer is the next PR reviewed via
`scripts/review.sh`. Both events occur within days: this repo judged
five FRs (FR-925…FR-929) in the preceding week.
**Research:** [FR-931.research.md](FR-931.research.md)
(brief: `feature-requests/research-briefs/fr931-model-pin-brief.md`;
run 2026-08-30T12:29:00Z, five personas; provenance line in
`feature-requests/research-runs.jsonl`, verified `matching` by
`scripts/research_preflight.py --verify-promotion`)
**Prior art:** the filename-noun gate hit only generic "model"/"pin"
token overlaps (corpus/census briefs, session receipts, web-research
fail-open) — none concerns which model executes a governed route. The
real prior art is FR-758 / CAP-211 (the wrapper + adapter contract this
FR edits), FR-266 (the model resolution chain it relies on), and FR-928
(in-flight, pins the same literal as an invariant); all three are
dispositioned under Related. No prior FR proposes changing the
judge/review pin — this is the first.

## Summary

Change one literal in each of two files —
`.github/skills/judge-fr/adapters/graph.yaml` and
`.github/skills/review-pr/adapters/graph.yaml` — from
`cli_flags.model: gpt-5.5` to `cli_flags.model: gpt-5.6-sol`, and add
the mechanical witness that both sole routes carry an explicit,
identical pin. Evidence the change by executing each route once under
the new pin and recording the contract-valid artifacts.

## Value Statement

Every FR authority grant and every PR merge advisory in this repository
is rendered by one pinned model; moving that pin to the current
generation buys better verdicts at 2.5×/3× lower input/output token
price and a 272k (vs 200k) prompt window, while the added witness makes
the pin a tested contract instead of a copy-pasted literal.

## Problem

The judge and review routes pin `gpt-5.5`, chosen when it was the
strongest reasoning model the Copilot CLI served. It is now a
generation behind. `gpt-5.6-sol` is served by the same binary the
adapters shell out to (verified this session, CLI 1.0.82: `copilot -p
"reply with exactly: OK" --model gpt-5.6-sol --allow-all-tools`
completed and billed 7.55 credits), is cheaper per token, and carries a
larger default context — which matters because the judge reads a whole
FR plus doctrine plus cited files, and the reviewer reads a whole PR
diff.

Three facts make this more than a taste preference:

1. **Price.** From the committed price sheet
   (`feature-requests/FR-900-evidence.md:63-120`): `gpt-5.5` is
   `{in: 500, out: 3000}` credits/1M; `gpt-5.6-sol` is
   `{in: 200, out: 1000}` with a 0.3 auto-discount and a 272k default
   window (922k long-context). The governed spend gets cheaper, not
   more expensive — the constraint that the sole routes stay the cheap
   ~5% of the invoice (diary 2026-08-25) is satisfied, not strained.
2. **Verdict quality is load-bearing and has failed observably.** Five
   consecutive "Not approved" review rounds under the current pin ended
   in an operator merge
   (`docs/analysis-fr888-post-mortem-2026-08-25.md:17`).
3. **The pin is duplicated and untested.** Two adapters carry the same
   literal by copy-paste; no test asserts either is present, so a
   silent deletion would drop both routes onto the CLI's ambient
   default — "the drift surface nobody bills to a diff"
   (`docs/diary/diary-2026-08-25-the-invoice-audits-the-doctrine.md:60-65`).

## Ideal Result

The judge and review routes always run on the model the repository has
deliberately chosen; that choice is one line per adapter, visible in a
diff, asserted by a test, evidenced by a real contract-valid artifact
from each route, and revertible by a one-line change. Changing the pin
is an ordinary FR, not an unrecorded act.

## Proposed Solution

Minimal path back from the ideal, in three moves.

**1. The pin (two lines).**

```yaml
# .github/skills/judge-fr/adapters/graph.yaml
# .github/skills/review-pr/adapters/graph.yaml
    cli_flags:
      model: gpt-5.6-sol      # was: gpt-5.5
      allow_all_paths: true
      allow_all_tools: true
```

Nothing else in either adapter changes: `backend: cli`, both `allow_*`
flags (NC-414: load-bearing for the file-write contract), `timeout:
600`, prompts, edges and state all stay.

**2. The witness (`tests/unit/test_fr931_sole_route_model_pin.py`).**
Two stdlib+YAML assertions, no API, no graph execution:

- both adapters set a non-empty `nodes.<node>.cli_flags.model` — guards
  the un-pinning drift surface;
- the judge pin equals the review pin equals `gpt-5.6-sol` — guards
  divergence between the twin routes and makes any future pin change
  pass through an FR (the test must be edited deliberately).

This is a genuine RED: the assertion fails against today's `gpt-5.5`.
Commit RED then GREEN per Commandment 7.

**3. The evidence (two executed runs, recorded in this FR).**
Verification is by artifact, never exit code:

```bash
scripts/judge.sh tests/fixtures/fr890/FR-998-fixture-missing-research.md
# → tmp/draft-judgement.md, contains a "**Verdict:**" line
scripts/review.sh <this PR> feature-requests/FR-931-judge-review-model-pin-gpt56sol.md
# → tmp/draft-review.md, line one is "**Merge verdict:**"
```

The judge run uses the committed fixture whose expected outcome is
known — `tests/fixtures/fr890/FR-998-fixture-missing-research.md` must
NOT be granted authority (it lacks the `**Research:**` field, see the
committed golden
`tests/fixtures/fr890/FR-998-fixture-missing-research.judgement.md`).
That is a substance check, not a shape check: it asks whether the new
model still enforces the research gate, not merely whether it writes a
file.

**Registry.** Add `REQ-YG-632` to `CAP-211-sole-route-judge-review.yaml`
for the explicit-pin invariant, naming the two adapter graphs and the
new test module; tag the test `@pytest.mark.req("REQ-YG-632")`.

**Not authorized by this FR:** the authoring adapter
(`.github/skills/graph-authoring/adapters/graph.yaml`) keeps `gpt-5.5`.
Authoring is a different task shape (it writes and lints graph
artifacts, not verdicts) and was not in the requested scope; the pin
test therefore asserts judge/review equality only, so the authoring
route may diverge deliberately. A separate FR may repoint it once the
judge/review pin has real run history.

## Acceptance Criteria

- [ ] AC-01: `tests/unit/test_fr931_sole_route_model_pin.py` exists, is
      tagged `@pytest.mark.req("REQ-YG-632")`, and asserts that both
      `.github/skills/judge-fr/adapters/graph.yaml` and
      `.github/skills/review-pr/adapters/graph.yaml` define a non-empty
      `cli_flags.model` on their single copilot node.
- [ ] AC-02: the same test asserts both pins are equal to each other and
      equal to `gpt-5.6-sol`.
- [ ] AC-03: git history shows the test committed RED (failing against
      `gpt-5.5`, `SKIP=pytest`) before the adapter edit that turns it
      GREEN.
- [ ] AC-04: the two adapter files differ from `main` in exactly one
      line each (`git diff --numstat` reports `1 1` per file).
- [ ] AC-05: `yamlgraph graph lint` reports no new issues for both
      adapter graphs.
- [ ] AC-06: a real `scripts/judge.sh` run against
      `tests/fixtures/fr890/FR-998-fixture-missing-research.md` under the
      new pin produced a `tmp/draft-judgement.md` satisfying the
      wrapper contract (non-empty, `**Verdict:**` line present); the
      verdict withholds authority for missing research, and the log path
      plus verdict line are quoted in this FR's implementation record.
- [ ] AC-07: a real `scripts/review.sh` run against this FR's own PR
      under the new pin produced a `tmp/draft-review.md` whose line one
      is `**Merge verdict:**`; log path and verdict line quoted in this
      FR.
- [ ] AC-08: `CAP-211-sole-route-judge-review.yaml` gains `REQ-YG-632`
      naming both adapter graphs and the new test module;
      `python scripts/req_coverage.py --strict` passes.
- [ ] AC-09: changelog fragment in `changelog/unreleased/` with
      `type: chore` (or `feat`), `scope: judge`, `req: REQ-YG-632`,
      recording the pin change and its price delta.
- [ ] AC-10: the authoring adapter's `gpt-5.5` pin is unchanged
      (`git diff` shows no modification to
      `.github/skills/graph-authoring/adapters/graph.yaml`).
- [ ] AC-11: diary reflection committed in `docs/diary/`.

## Alternatives Considered

Dispositioned from `feature-requests/FR-931.research.md` (five personas,
run 2026-08-30):

| # | Candidate (persona) | Disposition |
|---|---|---|
| A1 | Extract the pin into a shared `config/models.yaml` referenced by both adapters via YAML anchor/include (os-infra-primitivist, *pursue*) | **Rejected — premature abstraction.** Two call sites, one owner, and the pin-equality test already makes divergence a failing test rather than a silent bug. A shared file adds a load path to graphs whose entire value is being thin, doctrine-free pointers. Revisit at three or more consumers. |
| A2 | Version the pin in a `defaults.model` block with a changelog entry, cost attestation, and a mandatory test run before merge (data-process-planner, *pursue*) | **Partially adopted.** The changelog entry (AC-09), the cost line (Problem §1), and the tested-before-merge rule (AC-06/AC-07) are taken. The `defaults.model` relocation is rejected: `cli_flags.model` is the highest-priority link in the resolution chain (FR-266) and moving the pin down the chain makes the effective model less obvious, not more. |
| A3 | Add a deterministic availability gate node that verifies the model is served before execution, plus a shared data_file (yamlgraph-native-planner, *pursue*) | **Rejected — the failure is already legible.** An unserved model identifier makes the CLI fail and the wrapper exit 65 with "contract violated … `tmp/draft-judgement.md` missing" — loud, not silent. A pre-flight probe would spend tokens per run to predict a failure the artifact contract already catches. |
| A4 | Delete the pin entirely and inherit from the resolution chain (subtractionist, *dissent*) | **Rejected, and the dissent is preserved because it is right about the shape of the problem:** the duplication is real. It is forbidden by the brief's own constraint — an unpinned node inherits the CLI ambient default and becomes an unbilled drift surface (diary 2026-08-25). AC-01 turns this from doctrine into a test. |
| A5 | Adopt `modelpin` (`https://github.com/samarthputhraya/modelpin`): detect provider model churn, replay real behaviour on the candidate model, and post a PR-style regression report (librarian, *pursue*) | **Rejected as tooling, adopted as method.** The tool's premise is exactly right — a pin change must be evidenced by replayed real behaviour against a frozen contract, not asserted. But it needs a golden dataset and a replay harness, and this repo already has both in miniature: a committed golden fixture (`tests/fixtures/fr890/FR-998-fixture-missing-research.md` + its expected judgement) and a frozen artifact contract the wrappers already enforce. AC-06 is that replay, done by hand, once. Revisit the tool if the pin starts changing on the vendor's schedule rather than ours. |

Also considered and rejected: doing nothing. The pin is a decision that
was made once and never re-examined; leaving it costs more per token
than the alternative and leaves both routes untested against
un-pinning.

## Risk and rollback

Single risk: the new model renders worse verdicts. Detection is AC-06
(does it still enforce the research gate?) plus the next few real
judgements. Rollback is one line per adapter plus one line in the test
— cheaper than the FR that proposes it.

## Related

- `feature-requests/FR-758-judge-review-traceability-reconstruction.md`
  / `capabilities/CAP-211-sole-route-judge-review.yaml` — the wrapper
  and adapter contract this FR edits.
- `feature-requests/FR-928-cloud-judge-github-actions.md:227` —
  **coordination required.** FR-928 holds "same model pin (`gpt-5.5`)"
  constant to isolate cloud-vs-local variance. Whichever merges second
  must restate the invariant as "the pin currently in the adapter", not
  the literal `gpt-5.5`; FR-928's comparison remains valid as long as
  both sides read the same adapter.
- FR-266 — copilot node model resolution chain
  (`cli_flags.model` > node `model` > `defaults.model` > omit).
- `docs/diary/diary-2026-08-25-the-invoice-audits-the-doctrine.md` — the
  invoice-as-coverage-report reading; also records an unexecuted repoint
  lever for `.chaplain/graphs/watcher-enforce/validate-session.yaml`
  (Opus 4.6 → cheaper), still open, out of scope here.
- `feature-requests/FR-900-evidence.md` — committed price sheet used for
  the cost comparison.
- `docs/analysis-fr888-post-mortem-2026-08-25.md:17` — five review
  rounds under the current pin.
- **Research-route robustness observation (not scope, candidate FR):**
  producing this research record took 7 runs of `scripts/research.sh`,
  of which 5 failed. Failure modes, all downstream of one persona cell:
  twice `precedent cites nonexistent path:
  'examples/demos/data-files-demo/graph.yaml'` (the real path is
  `examples/demos/data-files/graph.yaml` — a persona appends `-demo`),
  once `precedent names unknown Scripture key or committed dir:
  'data_files'`, once a `LibrarianFinding.rationale` over its
  400-character bound, once `missing persona findings:
  librarian_finding`. The reducer is right to reject hallucinated
  precedents; the cost is that one bad cell discards four good findings
  and the whole run's tokens — a per-persona quarantine (drop the row,
  keep the run, record the drop) would convert a hard failure into
  recorded disagreement. Failure logs are local and uncommitted
  (`logs/` is gitignored: `logs/fr931-research*.log`); only successes
  append to `feature-requests/research-runs.jsonl`, so the ~70% failure
  rate leaves no committed trace — the run log is a survivor record.
- Row 4 of the promoted research record carries a corrupted trailing
  cell (`</anionale> </invoke>`) — model emission artifact, left
  unedited to preserve the promotion hash.

## Judgement (pending)

Not yet judged. Route: `scripts/judge.sh
feature-requests/FR-931-judge-review-model-pin-gpt56sol.md` — which will
run under the OLD pin (`gpt-5.5`), as it must: the authority to change
the pin is granted by the incumbent.
