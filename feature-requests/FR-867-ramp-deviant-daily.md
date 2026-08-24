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

- [x] AC-01: FR-867 is revised to define dependency activation evidence, exact install command/asset set, draft-review handoff, CI-block semantics, target RTM identity, and cross-repo transcript requirements from R-1 through R-6.
- [x] AC-02: Before any target write, FR-867 records the target repo URL/path, branch, exact HEAD, clean target git status, clean yamlgraph git status for relevant files, and the explicit file list expected to change in each repo. *(resolved — see Execution Record)*
- [x] AC-03: Before any target write, FR-867 records the yamlgraph commit SHA and validation evidence for the enforced FR-865 installer assets and the enforced FR-866 graph draft artifacts; both sibling judgements' revision gates are satisfied.
- [x] AC-04: The chosen install path is exact: either `scripts/ramp.sh <target> --tier 3` or `scripts/ramp.sh <target> --tier 2` plus an explicitly listed RTM asset subset. The dry-run transcript is pasted into FR-867 before install and shows the planned target paths.
- [x] AC-05: The curated ramp manifest and enforcement asset set have a recorded human-review approval before first non-scratch use against `deviant-daily`. *(approved 2026-08-24 — see FR-865 AC-14 record; reviewed_sha `cea3e49f`)*
- [x] AC-06: The installer writes only the approved paths from AC-04; the install transcript records created/skipped/overwritten actions and source commit SHA without secrets. *(logs/fr867-install.log — 20 create, 0 skip/overwrite)*
- [x] AC-07: After install, `.git/hooks/pre-commit` exists in the target and `pre-commit run --all-files` executes; the target transcript records command, exit status, and non-secret summary. *(logs/fr867-precommit.log — green on third pass)*
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
fails the pipeline costs a post. AC-16 makes the next successful cron
run a hard criterion, and the ramp installs no gate that runs inside the
publish workflow.

**RTM theatre.** 145 tests may not yield 10 defensible requirements. If
they do not, record it — a short honest registry beats a padded one.

**Cross-repo index collisions.** Two repos, one operator, parallel
sessions. AC-02/AC-19 and parent C-6 make boundaries explicit; work in
one repo at a time with explicit file lists.

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

## Execution Record (2026-08-23, up to the human gates)

### Activation record (R-1) — all four artifacts recorded

| Artifact | Evidence |
|---|---|
| FR-865 judgement | `feature-requests/FR-865-ramp-installer.judgement.md` — authority granted, revisions folded; enforced RED `c92b18f3` / GREEN `cea3e49f` |
| `scripts/ramp.sh` + `ramp/manifest.yaml` | committed in `cea3e49f`, tests green |
| FR-866 judgement | `feature-requests/FR-866-ramp-tailoring-graphs.judgement.md` — authority granted, revisions folded; enforced RED `3dae424c` / GREEN `8e34f4de` |
| `examples/demos/ramp_{doctrine,rtm,incidents}/graph.yaml` | committed in `8e34f4de`, lint clean (witnessed by `test_graph_lints_clean` ×3) |

### AC-02 status — RESOLVED (2026-08-24)

The original block stands as history below; the operator resolved it by
committing the WIP in the target (`3f83bc02` "chore: tests") and
authorized install via the gate questionnaire ("Install anyway on dirty
tree" — moot by install time: `git status --short` in the target was
**empty** immediately before install).

- Target: `/Users/sheikki/Documents/src/deviant-daily`
  (`https://github.com/sheikkinen/deviant-daily`), branch `main`,
  HEAD `3f83bc02e9dd373489ea95e82b48168ddd5ddc97`, status clean
  (snapshot: `tmp/fr867-target-status-before.txt`, 0 lines).
- YAMLGraph at `560a27145f3d`; ramp assets unchanged since `cea3e49f`.
- Expected target changes: exactly the 20 AC-04 create paths plus
  `docs/ramp-manifest.md` (installer-written). Expected yamlgraph
  change: one row in `ramp/consumers.md`.

### Original AC-02 block (historical, 2026-08-23)

Ran in: **yamlgraph** (read-only against target).

- Target: `/Users/sheikki/Documents/src/deviant-daily`
  (`https://github.com/sheikkinen/deviant-daily`), branch `main`,
  HEAD `cbdc81b7e308486be7071c6bd4e49cd5996bddeb` (matches the FR's
  authoring-time HEAD — no new commits landed).
- **Target `git status -sb` is NOT clean**: 15 modified files
  (`.github/workflows/daily.yml`, `.gitignore`, `README.md`,
  `pyproject.toml`, 4 test files, 7 `tools/*.py`) + untracked `logs/`
  — foreign in-progress work, −342/+106 lines. Not this session's WIP;
  per `workspace_is_not_boundary` it will not be stashed, committed,
  or reverted by this FR. **Install does not proceed until the
  operator resolves the target tree.**

### AC-04 dry-run transcript (read-only; verified nothing written)

Ran in: **yamlgraph**, `scripts/ramp.sh ~/Documents/src/deviant-daily --tier 3 --dry-run`
(full log: `logs/fr867-dryrun.log`; target status identical before/after):

```
dry-run: tier 3 into /Users/sheikki/Documents/src/deviant-daily — nothing will be written
create .pre-commit-config.yaml
create .github/hooks/pre-command-guard.json
create .github/hooks/scripts/pre-command-guard.sh
create .github/hooks/README.md
create .github/workflows/tests.yml
create AGENTS.md
create feature-requests/TEMPLATE.md
create .github/skills/judge-fr/SKILL.md
create .github/skills/judge-fr/doctrine.md
create .github/skills/judge-fr/judgement.template.md
create .github/skills/review-pr/SKILL.md
create .github/skills/review-pr/doctrine.md
create .github/skills/review-pr/review.template.md
create scripts/judge.sh
create scripts/review.sh
create scripts/gates/changelog_gate.sh
create scripts/gates/diary_gate.sh
create docs/diary/TEMPLATE.md
create capabilities/README.md
create scripts/req_coverage.py
```

Chosen install path: `scripts/ramp.sh /Users/sheikki/Documents/src/deviant-daily --tier 3`.

### AC-08 graph runs (fresh, against target HEAD working tree)

Ran in: **yamlgraph** at `412b4c68`; graphs write only `tmp/ramp/`.
An earlier pair of drafts was overwritten by FR-866's fixture demo runs;
these are regenerated against the real target (freshness matters —
draft provenance is part of the record):

| Draft | Command var | sha256 (12) | Content |
|---|---|---|---|
| `tmp/ramp/doctrine-draft.md` | `target=<path>` | `6e03df7a0ff2` | 29 of 55 Scripture entries kept; zero foreign FR/NC citations (AC-09 precondition holds) |
| `tmp/ramp/rtm-draft.md` | `target=<path>` | `3e40d715d571` | 51 REQ candidates from 108 inventoried tests; 25 gap tests honestly listed; 0 validation errors |
| `tmp/ramp/incidents-draft.md` | `target_name=deviant-daily` | `686e86a2eff5` | 10 incidents from 33 corpus docs, incl. all four 2026-08-23 failures (FR-863) |

Note: RTM inventoried 108 tests vs the baseline's 145 — the dirty
working tree modifies 4 test files; re-run after the tree is resolved
if the count matters to the review.

### Human-review handoff table (R-3 / AC-09) — awaiting reviewer

| Draft | Hash | Reviewer | Date | Disposition per section | Final target path |
|---|---|---|---|---|---|
| `tmp/ramp/doctrine-draft.md` | `6e03df7a0ff2` | *(pending)* | | | `AGENTS.md` (planned) |
| `tmp/ramp/rtm-draft.md` | `465708c3d04a` | *(pending)* | | | `capabilities/` + test tags (planned) |
| `tmp/ramp/incidents-draft.md` | `686e86a2eff5` | *(pending)* | | | `docs/incidents.md` (planned) |

RTM re-run (2026-08-24) against clean target HEAD `3f83bc02`:
**80 REQ candidates / 108 tests / 0 gaps / 0 validation errors**
(`logs/fr867-rtm-rerun.log`); the dirty-tree draft (`3e40d715d571`,
51/108/25) is archived at `tmp/ramp/archive-cbdc81b7/`. The baseline's
145-test count did not survive the operator's "chore: tests" commit —
AC-13's "at least 145" needs revision or the target suite regrew; flag
for the AC-13 witness step.

### Review note carried from FR-866 (AC-15 raw read)

`collect_inventory` does not surface a root `graph.yaml`, so the
`is_this_a_graph` question was judged `not applicable` against the
fixture — verify the doctrine draft's question dispositions against
the real target before landing.

### Install record (AC-06/AC-07, 2026-08-24)

- Command: `scripts/ramp.sh ~/Documents/src/deviant-daily --tier 3
  --record-consumer sheikkinen/deviant-daily`, exit 0
  (`logs/fr867-install.log`): 20 `create` actions, 0 skip/overwrite,
  source `560a27145f3d`, manifest `fcdee1b04548`; consumer row written
  to `ramp/consumers.md`.
- `pre-commit install` + `pre-commit run --all-files`
  (`logs/fr867-precommit.log`): pass 1 — ruff-format reformatted 18
  files; pass 2 — trailing-whitespace fixed 2 logs; pass 3 — **all
  hooks green, exit 0**. `.git/hooks/pre-commit` exists and is
  non-empty.
- Target commit `e9595b6` — 41 files (20 installed + manifest +
  first-contact fixer pass), gated by the target's own freshly
  installed hooks.

### Remaining steps

> **Gap attribution:** FR-872's disposition table
> (`feature-requests/FR-872-investigate-incomplete-ramp-install.md`,
> Implementation Record) attributes every post-install gap: rows 4–7
> are FR-867 steps 4–6 below (AC-09..AC-13), row 8 adds a step — the
> target must author its own judge/review adapter graphs per the
> installed `doctrine.md` before it can govern its own FRs — and rows
> 8/9's installer-defect components route to an FR-865 follow-up, not
> here.

1. ~~Operator: resolve dirty target tree~~ — done (`3f83bc02`).
2. ~~Operator: AC-05 approval~~ — done (2026-08-24 questionnaire).
3. ~~Install (`--tier 3`), transcript per R-6~~ — done (AC-06/07, target commit `e9595b6`).
4. Draft review rows filled → land `AGENTS.md`, registry (`REQ-DD-XXX`), `docs/incidents.md` → AC-09/10/11.
5. Tag tests / record gaps → AC-12.
6. Enable CI, witness push run → AC-13 (baseline needs revisit: clean tree has 108 tests, not 145).
7. Blocked-commit witness + CI-detects witness → AC-14/15 (AC-15 stays "detected by CI" unless a branch-protection FR lands).
8. Next cron green → AC-16; secret/direction scan → AC-17; FR-863 cross-refs → AC-18; dual clean statuses → AC-19.
