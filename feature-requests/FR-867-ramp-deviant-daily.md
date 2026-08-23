# Feature Request: Ramp deviant-daily to Tier 2 + RTM

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.25 day
**Requested:** 2026-08-23
**Parent:** FR-864 (SPLIT) — child C per R-4
**Depends on:** FR-865 (installer) and FR-866 (graphs) having their own
granted authority and working artifacts.
**First consumer / first event:** the operator. First event: a commit to
`sheikkinen/deviant-daily` that deliberately violates a gate and is
**blocked locally** — the first time that repo has ever said no.

**Prior art:** **FR-826** created the target repo and froze its corpus,
ledger and roster contracts — this FR adds governance around it and
changes none of them. **FR-862** added its dispatch surface and is
partially superseded; non-overlapping here. **FR-863** is the incident
record this ramp repatriates and the evidence that the repo needs gates:
four production failures on 2026-08-23. **FR-865/FR-866** are the tools;
this FR is their first application and must not re-specify them. No
REJECTED prior art occupies this territory.

## Summary

Apply the ramp to `sheikkinen/deviant-daily`: Tier 2 plus the Tier 3
RTM, with its doctrine, requirement registry and incident record derived
by FR-866's graphs and reviewed before landing.

## Value Statement

The repo that publishes daily to a public gallery stops being the one
repo in the estate where nothing says no.

## Problem

`deviant-daily` went to production on 2026-08-19 (commits `71e80b9`
first public publish, `eeca704` cron enabled). As of 2026-08-23 it has:

- **0** pre-commit hooks (`.git/hooks/` empty; ~10 commits ran unvalidated)
- **0** CI jobs running its **145** tests across 14 files
- **0** doctrine file
- **4** production failures in one morning, whose record is filed in
  *this* repo rather than in it

It is Tier 2 by the money-or-reputation clause — it spends Replicate and
Anthropic tokens unattended and publishes under the operator's name. The
operator has additionally requested the Tier 3 RTM.

## Ideal Result

Tomorrow's cron runs unchanged. A commit that breaks style, hides a
failure, or lands without a diary entry is refused locally and in CI.
`AGENTS.md` describes *that* repo's boundaries — DeviantArt's API,
Replicate's providers, the vision payload ceiling — and cites its own
four incidents, which now live there. A reader learns why `MAX_EDGE =
1568` from the repo that learned it.

## Proposed Solution

### Target

Repository `sheikkinen/deviant-daily`, ref: the `main` HEAD at
enforcement time (recorded in the FR before work starts). Current HEAD
at authoring: `cbdc81b`.

### Steps

1. `scripts/ramp.sh <target> --tier 2 --dry-run`; review the plan.
2. Install Tier 2, then the Tier 3 RTM subset (registry shape,
   `req_coverage.py`, `--strict` gate).
3. Run FR-866's three graphs against the target; review the three drafts
   in `tmp/ramp/`.
4. Land the reviewed drafts as `AGENTS.md`, `capabilities/*.yaml`,
   `docs/incidents.md` in the target.
5. Tag existing tests with requirement IDs until `req_coverage --strict`
   passes or the gaps are recorded as known.
6. Enable the CI workflow; witness it running 145 tests on push.
7. Witness a blocked commit.

### Baseline to record before starting

| Metric | Value at `cbdc81b` |
|---|---|
| test files / tests | 14 / 145 |
| pre-commit hooks | 0 |
| CI jobs running tests | 0 |
| requirement tags | 0 |
| documented incidents | 0 (4 filed in yamlgraph) |

## Acceptance Criteria

Exhaustive for this surface alone; assumes FR-865/866 delivered.

- [ ] AC-01: the target ref is recorded in this FR before any change.
- [ ] AC-02: `--dry-run` output is pasted into the FR before install.
- [ ] AC-03: after install, `.git/hooks/pre-commit` exists in the target
      and `pre-commit run --all-files` executes.
- [ ] AC-04: the target's CI runs its full suite on push; witnessed by
      run id, with the test count reported ≥ 145.
- [ ] AC-05: a deliberately non-conforming commit is **blocked locally**;
      transcript recorded (non-secret).
- [ ] AC-06: a deliberately non-conforming push is **blocked in CI**;
      run id recorded.
- [ ] AC-07: `AGENTS.md` exists in the target, is the reviewed
      `ramp_doctrine` draft, contains zero foreign witness citations,
      and names ≥ 1 target-specific boundary.
- [ ] AC-08: `docs/incidents.md` exists in the target containing all
      four 2026-08-23 failures with root cause and cure.
- [ ] AC-09: a requirement registry exists in the target; every entry
      carries `status` and ≥ 1 witness test that exists.
- [ ] AC-10: `req_coverage --strict` either passes or its gaps are
      enumerated in the FR as accepted, with a reason per gap.
- [ ] AC-11: **the scheduled publish still works** — the first cron run
      after the ramp completes green, recorded by run id and ledger row.
      This is the regression that matters; gates must not break the
      product.
- [ ] AC-12: no secret, token, or token-bearing log is copied in either
      direction; asserted by scanning the diff.
- [ ] AC-13: `deviant-daily` is **not** vendored, submoduled, archived,
      or committed into yamlgraph; `git status` in both repos is clean
      and separate at completion.
- [ ] AC-14: the four incidents' entries in yamlgraph's FR-863 gain a
      cross-reference to their new home (repatriation, not duplication).

## Risks

**The ramp breaks the product.** The repo publishes daily; a gate that
fails the pipeline costs a post. AC-11 makes the next successful cron
run a hard criterion, and the ramp installs no gate that runs inside the
publish workflow.

**RTM theatre.** 145 tests may not yield 10 defensible requirements. If
they do not, record it — a short honest registry beats a padded one.

**Cross-repo index collisions.** Two repos, one operator, parallel
sessions. AC-13 and parent C-6 make boundaries explicit; work in one
repo at a time with explicit file lists.

**Doctrine drift on day one.** `AGENTS.md` will be wrong in places. It
is a draft that gets corrected by incidents — which is the mechanism,
not a defect.

## Alternatives Considered

- **Tier 1 only.** Rejected: the repo has already had incidents that
  cost publication and reputation; that is the Tier 2 trigger by
  definition.
- **Wait until FR-865/866 have several other consumers.** Rejected: this
  repo is the reason both exist, and a tool with no first consumer is
  `growth_as_default`.
- **Hand-install without the ramp.** Rejected: it would leave the ramp
  untested by its own first case.

## Related

- `feature-requests/FR-864-ramp-spike-to-governed.md` (parent, SPLIT) and its judgement
- `feature-requests/FR-865-ramp-installer.md`, `feature-requests/FR-866-ramp-tailoring-graphs.md`
- `feature-requests/FR-826-deviantart-daily-repo.md` — target repo contracts, unchanged here
- `feature-requests/FR-863-deviant-daily-publish-policy-boundary-mirroring.md` — the four incidents
