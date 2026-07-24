# Feature Request: Post-fact CAP/REQ/test reconstruction for judge-fr / review-pr bundles

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged
**Effort:** 0.5 day
**Requested:** 2026-07-24
**First consumer / first event:** the next agent invoking
`scripts/judge.sh` or `scripts/review.sh` after any edit to the
wrappers or adapters — the witness tests catch the regression at
commit time instead of mid-judgement; `scripts/req_coverage.py` gains
the REQ the moment CAP-211 lands.

## Summary

The judge-fr and review-pr skill bundles (`.github/skills/judge-fr/`,
`.github/skills/review-pr/`) and their operational wrappers
(`scripts/judge.sh`, `scripts/review.sh`) were adopted as mirror
copies from csap (PRs #460, #461; lineage NC-412/413/414/415). They
carry no CAP entry, no REQ-YG requirement, and zero local tests. This
FR reconstructs the traceability spine post-fact and mechanizes the
wrapper contract as witness tests. No behavior change.

## Value Statement

The repository's governance boundary (sole-route judge/review) becomes
locally witnessed instead of inherited on faith — a regression in the
wrappers fails a test here, not a judgement in production.

## Problem

A 2026-07-24 verification (diary:
`docs/diary/diary-2026-07-24-route-contract-is-not-hook-contract.md`)
found the implementation locally coherent but **inherited, not
witnessed**:

- No CAP in `capabilities/` and no REQ-YG covers the sole-route
  judge/review execution contract (next free: CAP-211, REQ-YG-569).
- Zero local tests: `grep -rn "judge.sh|review.sh|JUDGE_EXECUTION|
  REVIEW_EXECUTION" tests/ .github/hooks/tests/` is empty.
- The wrappers had never been executed in this repository after
  porting; `bash -n` passes, but syntax is not behavior (BSD vs GNU
  `find -mmin`, lock-dir semantics, artifact grep anchors were all
  plausible porting hazards).

Scripture: provenance is not proof; `detection_without_enforcement`;
a mirror copy needs a mirror witness before this repo relies on it as
a governance boundary.

## Ideal Result

Every mechanical guarantee the wrappers claim (serialization,
recursion denial, executor resolution, artifact contract) is asserted
by a fast local test tied to REQ-YG-569 in CAP-211, and one recorded
real execution proves the ported scripts run end-to-end on this
platform — so the sole-route contract is enforced by the same
traceability spine as every other capability.

## Proposed Solution

1. **CAP-211** — `capabilities/CAP-211-sole-route-judge-review.yaml`,
   status active, `fr: FR-758`, describing the sole-route contract:
   wrapper serializes (atomic `mkdir` lock, 10-min stale detection),
   recursion sentinels `JUDGE_EXECUTION`/`REVIEW_EXECUTION`, explicit
   executor resolution (`YAMLGRAPH_BIN` → PATH `yamlgraph` → `uv run`
   → fail 69), artifact contracts (`tmp/draft-judgement.md` must
   contain a `**Verdict:**` line; `tmp/draft-review.md` must have
   `**Merge verdict:**` as line one), advisory-draft output.
   Modules: `scripts/judge.sh`, `scripts/review.sh`,
   `.github/skills/judge-fr/adapters/graph.yaml`,
   `.github/skills/review-pr/adapters/graph.yaml`.
2. **REQ-YG-569** inside CAP-211; all new tests tagged
   `@pytest.mark.req("REQ-YG-569")`.
3. **Wrapper contract tests** — `tests/unit/test_fr758_judge_review_wrappers.py`
   (`process` marker, stub `YAMLGRAPH_BIN` script, tmp workdir via
   `JUDGE_WORKDIR`/`REVIEW_WORKDIR`; no real judge run, no API keys):
   - usage / missing-FR exits (64, 66)
   - recursion sentinel denial (exit 70), both wrappers
   - lock held → 73; stale lock (>10 min, backdated mtime) → 75 with
     holder info; lock removed on normal exit (trap)
   - executor resolution: `YAMLGRAPH_BIN` honored; fail 69 when
     nothing resolves (scrubbed PATH)
   - artifact contract: missing/empty artifact → 65; missing verdict
     line → 65; review merge-verdict not on line one → 65
   - success path: stub writes conforming artifact → exit 0
4. **One real smoke execution** of each wrapper, recorded in this FR
   with exact evidence fields (R-2): command, timestamp, executor
   identity (`YAMLGRAPH_BIN` / PATH `yamlgraph` / `uv run yamlgraph`),
   exit code, artifact path, and artifact head proving the contract
   (`**Verdict:**` for judge; `**Merge verdict:**` on line one for
   review). The review smoke must record its PR/branch input. Manual
   evidence only — never an automated test or CI step.
5. **`ARCHITECTURE.md` traceability** (R-1): capability summary row
   after CAP-210 and a CAP-211 section with a REQ-YG-569 row, matching
   the CAP-210 shape — required for `req_coverage.py --strict`.
6. **Changelog fragment** in `changelog/unreleased/` with
   `req: REQ-YG-569`.

## Evidence: manual probes already pass (2026-07-24)

Nine stub-executor probes were run manually on macOS during planning;
all matched contract: judge usage=64, missing-FR=66, sentinel=70 (both
wrappers), stub success=0 with lock cleanup, lock contention=73,
missing-verdict-line artifact=65, review verdict-line-one enforced.
Scope item 3 mechanizes these probes; the residual unknown is only the
real-graph smoke (scope item 4).

## Acceptance Criteria

(Revised per judgement AC-01..AC-09; the judgement's list is binding.)

- [ ] `capabilities/CAP-211-sole-route-judge-review.yaml` exists,
      active, references FR-758, defines REQ-YG-569, names both
      wrappers and both adapter graphs
- [ ] `ARCHITECTURE.md` has the CAP-211 summary row and section with
      REQ-YG-569; `python scripts/req_coverage.py --strict` passes
- [ ] `tests/unit/test_fr758_judge_review_wrappers.py` module-marked
      `process`, every test tagged `@pytest.mark.req("REQ-YG-569")`,
      stub `YAMLGRAPH_BIN`, no API keys (placed under `tests/unit/`,
      not `.github/hooks/tests/` — req coverage excludes hook tests)
- [ ] Wrapper tests cover: usage/missing-FR exits, sentinel denial
      (both wrappers), active-lock + stale-lock behavior, lock cleanup,
      `YAMLGRAPH_BIN` precedence, resolution-failure exit 69,
      missing/empty artifact 65, verdict-line 65, review line-one
      merge-verdict 65, stub success 0
- [ ] Manual smoke evidence per R-2 recorded in this FR
- [ ] Changelog fragment with `req: REQ-YG-569`
- [ ] No wrapper/adapter/doctrine/hook/CI behavior change unless a RED
      witness first proves a porting defect; any enforcement-
      infrastructure change receives explicit human review before
      merge (R-3 GATE)

## Alternatives Considered

- **Hook-layer denial of manual judge/review execution** — rejected:
  a hook cannot observe the bypass (no tool event distinguishes a
  manual judgement from ordinary editing). The advisory boundary is
  accepted and documented in the diary entry.
- **Do nothing (trust csap provenance)** — rejected: provenance is not
  proof; the wrappers guard the authority boundary of the whole
  plan-judge-enforce pipeline.

## Related

- PRs #460, #461 (bundle adoption); csap NC-412/413/414/415 (lineage)
- `docs/diary/diary-2026-07-24-route-contract-is-not-hook-contract.md`
- `changelog/unreleased/judge-fr-skill-adoption.md`,
  `changelog/unreleased/review-pr-skill-adoption.md`
- FR-756 (process marker used by the new tests)

**Prior art:** FR-560 (dm-v3-m1 belief lane projection grounding,
Enforced) — lexical hit on "review"/"reconstruction" only; it concerns
DM belief-state projection, not the judge/review governance wrappers.
No scope overlap; nothing inherited or superseded.

## Judgement (2026-07-24)

**Verdict:** APPROVED WITH REVISIONS — problem real, test-first repair
minimal; authority activates after R-1..R-3 folded (done above).
Rendered via the sole route (`scripts/judge.sh`, second run); full
draft artifact preserved as the binding text — scope table D-1..D-7,
AC-01..AC-09, conditions C-1..C-6.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| R-1 | `req_coverage.py --strict` requires ARCHITECTURE.md rows the FR never authorized | ARCHITECTURE.md added to scope (item 5) and ACs |
| R-2 | "One real smoke execution" too vague to audit; review smoke needs a PR/branch input | Exact evidence fields pinned in scope item 4 |
| R-3 | FR permits wrapper fixes on porting defects without a human gate | Enforcement-infrastructure human-review GATE added to final AC |

**Purge list:** none.

**Scope frozen:** D-1..D-7 per judgement; not authorized: doctrine/
template/adapter-prompt/model changes, hook-layer denial, real
executions in CI, auto-fold/commit/PR/merge from adapters, moving
wrapper tests to `.github/hooks/tests/`, exit-code changes without a
RED witness + human gate.

**Note on the first judge run (forensic):** the first execution
rendered APPROVED WITH REVISIONS but could not persist its artifact —
every write was denied by a misregistered `PermissionRequest` hook
(fixed under RED/GREEN commits, see `tmp/judge-fr.log` forensics and
`changelog/unreleased/permission-request-decision-hook.md`). Its
recovered draft additionally proposed adapter-contract witness tests
(single copilot node, `backend: cli`, `allow_all_paths`,
`allow_all_tools`, `timeout: 600`); recorded here for the enforcer as
optional-but-cheap coverage consistent with the frozen scope (CAP
modules already name the adapter graphs).

### Questions for the human (as options, or 'none')

None — both judge runs converged on APPROVED WITH REVISIONS; the
revisions are mechanical and folded.
