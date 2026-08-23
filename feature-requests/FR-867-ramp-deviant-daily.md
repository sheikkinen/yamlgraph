# Feature Request: Ramp deviant-daily to Tier 2 + RTM

**Priority:** HIGH
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS (2026-08-23), R-1…R-6 folded
**Effort:** 0.25 day
**Requested:** 2026-08-23
**Parent:** FR-864 (SPLIT) — child C per R-4
**Activation record (R-1):** authority activates only when **all** of
these exist and are recorded here by path and commit SHA — vague
"readiness" is not a gate:

| Artifact | Required state |
|---|---|
| `feature-requests/FR-865-*.judgement.md` | verdict granting authority, revisions folded |
| `scripts/ramp.sh` + `ramp/manifest.yaml` | committed, tests green |
| `feature-requests/FR-866-*.judgement.md` | verdict granting authority, revisions folded |
| `examples/demos/ramp_{doctrine,rtm,incidents}/graph.yaml` | committed, lint clean |
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

1. `scripts/ramp.sh <target> --tier 3 --dry-run`; paste the plan here.
2. Install **Tier 3** (R-2). Tiers are monotonic in FR-865: Tier 3
   installs Tier 1 + Tier 2 + Tier 3. "Tier 2 plus an RTM subset" was
   ambiguous and is withdrawn — there is no partial-tier install. The
   asset set is exactly FR-865's Tier 3 manifest entries, listed here
   before execution.
3. Run FR-866's three graphs against the target; review the three drafts
   in `tmp/ramp/`.
4. **Recorded human-review handoff (R-3).** For each draft, this FR
   records: the draft path and hash, the reviewer, the date, the
   accepted/edited/rejected disposition per section, and the final
   landed path in the target. A draft that is landed unedited must say
   so explicitly. No generated governance file enters the target
   without its row in that table.
5. Tag existing tests with requirement IDs per the namespace below.
6. Enable the CI workflow; witness it running the suite on push.
7. Witness a blocked commit and a detected push (R-4).

### RTM identity and gap policy (R-5)

- Requirement namespace: **`REQ-DD-XXX`**, registry at
  `capabilities/CAP-XX-*.yaml` in the target, mirroring this repo's
  shape.
- Tag mechanism: `@pytest.mark.req("REQ-DD-XXX")`.
- **Allowed honest outcome:** if `req_coverage --strict` cannot pass
  truthfully, it is **not** forced to pass. Each gap is enumerated in
  this FR with a reason and one of `accepted` / `deferred-to-FR`. The
  gate is then either enabled in warn mode or left uninstalled, and
  which one is recorded. Padding the registry to make a gate green is
  forbidden.

### CI semantics: detection, not blocking (R-4)

`sheikkinen/deviant-daily` has **no branch protection and no required
status contexts**, and this FR does not add them — that is a repository
administration decision outside its scope. Therefore:

- **Local** pre-commit **blocks** — a non-conforming commit is refused.
- **CI detects** — a non-conforming push produces a red run; the push
  still lands.

The original criterion claimed CI "blocks". It would not have. Either
the operator later enables branch protection (its own FR), or the claim
stays "detects". This FR asserts only what is mechanically true.

### Cross-repo execution boundary (R-6)

Every command in this FR's execution record states which repository it
ran in. No command may stage or commit paths in both repositories. The
transcript records, per step: `cwd`, the repo, the explicit file list,
and `git status -sb` for **both** repos afterwards. Generated target
artifacts are never committed into yamlgraph, and yamlgraph's FR/diary
records are never committed into the target.

### Baseline to record before starting

| Metric | Value at `cbdc81b` |
|---|---|
| test files / tests | 14 / 145 |
| pre-commit hooks | 0 |
| CI jobs running tests | 0 |
| requirement tags | 0 |
| documented incidents | 0 (4 filed in yamlgraph) |
| branch protection / required contexts | none |

## Acceptance Criteria

Superseded by the judgement's revised set (2026-08-23); folded verbatim.

- [ ] AC-01: FR-867 is revised to define dependency activation evidence, exact install command/asset set, draft-review handoff, CI-block semantics, target RTM identity, and cross-repo transcript requirements from R-1 through R-6.
- [ ] AC-02: Before any target write, FR-867 records the target repo URL/path, branch, exact HEAD, clean target git status, clean yamlgraph git status for relevant files, and the explicit file list expected to change in each repo.
- [ ] AC-03: Before any target write, FR-867 records the yamlgraph commit SHA and validation evidence for the enforced FR-865 installer assets and the enforced FR-866 graph draft artifacts; both sibling judgements' revision gates are satisfied.
- [ ] AC-04: The chosen install path is exact: either `scripts/ramp.sh <target> --tier 3` or `scripts/ramp.sh <target> --tier 2` plus an explicitly listed RTM asset subset. The dry-run transcript is pasted into FR-867 before install and shows the planned target paths.
- [ ] AC-05: The curated ramp manifest and enforcement asset set have a recorded human-review approval before first non-scratch use against `deviant-daily`.
- [ ] AC-06: The installer writes only the approved paths from AC-04; the install transcript records created/skipped/overwritten actions and source commit SHA without secrets.
- [ ] AC-07: After install, `.git/hooks/pre-commit` exists in the target and `pre-commit run --all-files` executes; the target transcript records command, exit status, and non-secret summary.
- [ ] AC-08: The FR-866 graph runs used for this application record source commit SHA, command, draft paths, and draft hashes; no graph/tool writes directly into the target repo.
- [ ] AC-09: Before landing each generated governance artifact, FR-867 records draft path, draft hash, reviewer/date, accepted edits, final target path, and comparison statement. `AGENTS.md` names at least one target-specific boundary and contains zero foreign witness citations.
- [ ] AC-10: `docs/incidents.md` in the target contains all four 2026-08-23 failures from FR-863 -- vision payload ceiling, DA title cap, degenerate corpus key, and guard-flag hedging -- each with root cause, cure, and source reference.
- [ ] AC-11: The target requirement registry uses a target-local requirement prefix, every entry carries `status`, and every witness test name exists in the target.
- [ ] AC-12: Target tests are tagged with target-local requirement IDs until `req_coverage --strict` passes, or every strict gap is recorded with missing relation, reason, and human acceptance.
- [ ] AC-13: The target CI runs its full suite on push, with run id, commit SHA, command summary, and test count reported as at least 145.
- [ ] AC-14: A deliberately non-conforming target commit is blocked locally by pre-commit; the non-secret transcript records the failing hook and proves the deliberate change was not committed to `main`.
- [ ] AC-15: A deliberately non-conforming target change is blocked by a required CI merge gate using a throwaway branch or PR. If only a failing workflow run is available, the criterion is not satisfied unless FR-867 is revised to say "detected by CI" and branch protection is deferred to a separate FR.
- [ ] AC-16: The first scheduled publish after the ramp completes runs green; FR-867 records run id, commit SHA, and ledger row, proving the ramp did not break the daily product.
- [ ] AC-17: No secret, credential, token, token-bearing log, generated image, target repo archive, nested repo, or submodule is copied in either direction; the assertion is backed by a non-secret diff/status scan.
- [ ] AC-18: YAMLGraph's FR-863 gains cross-references from the four incident entries to their new target home, without duplicating target incident prose back into yamlgraph.
- [ ] AC-19: Completion records clean and separate git statuses for yamlgraph and `deviant-daily`, plus the final changed-file list for each repository.

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
