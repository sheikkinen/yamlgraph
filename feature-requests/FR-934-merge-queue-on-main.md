# Feature Request: Enable the GitHub merge queue on main — retire the rebase toll

**Priority:** HIGH
**Type:** Enhancement
**Status:** Enforcing — workflow wiring implemented (RED 4955c651 → GREEN, this PR); settings mutation pending operator review (C-2), then witness PRs
**Effort:** 0.5 days
**Requested:** 2026-08-30
**First consumer / first event:** the next two PRs opened from parallel
worktree lanes — instead of the second PR rebasing after the first
lands, both are enqueued with `gh pr merge` and the queue validates and
lands them in order. The event occurs within hours of merge: the
08-27..30 window landed ~78 commits from parallel lanes under the
rebase regime.
**Research:** [docs/plan-research-merge-queue.md](../docs/plan-research-merge-queue.md)
(committed 2026-08-30, PR #520 — platform-capability survey against
docs.github.com plus live repo-state evidence; equivalent committed
record per FR-890 R-6). Sole-route provenance note: `scripts/research.sh
feature-requests/research-briefs/fr934-merge-integration-toll-brief.md`
was run twice on 2026-08-30 and failed both times at the artifact
contract — the librarian_structure node exceeded the 400-char rationale
cap on all retries (graph rc=1, exit 65). The failure is recorded here
rather than routed around; the cap defect sits in FR-932's in-flight
territory (`examples/demos/research-route/nodes/research_tools.py`) and
is not patched by this FR. The brief is committed alongside this FR for
re-run when the route heals.
**Prior art:** FR-889 built the worktree → PR → squash substrate and its
§4d recorded the docs-PR deadlock (cured: the always-reporting no-op
step is live in `workflow.yml` `test` job; witnessed green on docs-only
PR #520, all three required contexts SUCCESS). FR-919 owns the doc-only
CI skip this FR must preserve. FR-902/FR-927 are the cautionary
precedent: they automated worktree provisioning — the cheap step — and
were retired in 72h with zero consumers; this FR targets the integration
boundary where the measured cost actually sits. No prior or REJECTED FR
proposes governing the merge boundary; `git log --grep` and a
feature-requests filename sweep found no merge-queue proposal.

## Summary

Enable GitHub's native merge queue on `main` (squash method), add the
`merge_group` trigger to the two workflows that carry required status
contexts, and disable `Require up to date (strict)` — the queue subsumes
it. Landing K parallel PRs stops costing O(K²) rebase+CI cycles and
zero manual rebases.

## Value Statement

Agents working in parallel worktrees stop paying a rebase and a full CI
re-run per previously-landed PR; the operator stops paying the
corresponding wall-clock time, LLM tokens, and money — named the single
largest process handicap.

## Problem

With `Require up to date (strict)` and N open PRs, every squash merge
invalidates the base of the other N−1 PRs; each must rebase and re-run
the matrix before it can land. The 08-27..30 window (78 commits, 20
worktrees, 13 stale merged lanes) paid this toll continuously. The
platform ships the cure: a merge queue provides "the same benefits as
the Require branches to be up to date before merging branch protection,
but does not require a pull request author to update their pull request
branch and wait for status checks to finish before trying to merge"
(docs.github.com, "Managing a merge queue"). The repo is public, so the
feature is on the free plan.

## Ideal Result

Two independently ready PRs are enqueued with plain `gh pr merge` and
never touch their head branches again: each required context reports on
the queue candidate, the queue lands both in order by squash, and if
queue validation cannot report, the repository returns to strict
protection via the recorded rollback. Zero manual rebases, zero
`--admin`, required checks gating reality.

## Research substance (judgement R-1)

`is_this_a_graph`: **No** — this is GitHub repository policy and CI
event wiring, not an LLM pipeline; no yamlgraph node is involved.

Preserved disagreement: the problem brief demanded docs-only PRs never
pay the full matrix end-to-end; the platform survey argues the merge
group is the integration boundary and should run everything. Both were
held until the R-2 human decision below resolved them — the
disagreement is recorded, not laundered.

## Human decisions (judgement R-2, R-4)

**R-2 docs-only cost policy — Option 1, PR-only saving
(judge-recommended):** docs-only PR validation stays cheap (the FR-919
path filter fires only on `pull_request` events, unchanged); the
merge-group candidate runs the full matrix because it is the last
validation before `main`. The FR-919 preservation claim is narrowed to
PR-event scope and the brief's constraint is amended to match.
Recorded as final by the operator's review and merge of this FR's PR.

**R-4 queue tuning:** slowest successful required-test run in the
preceding 24h was 6m29s (CI run for FR-931, 2026-08-30T13:22:38Z →
13:29:07Z); chosen safety margin ≈4×. Values: status-check timeout
**30 minutes**, wait for minimum group **1 minute**, min group size
**1**, max group size **5**, merge method **squash**,
only-merge-non-failing **enabled**. Recorded as final by the
operator's review and merge of this FR's PR.

## Proposed Solution

Three surfaces, smallest sufficient change on each:

### 1. `merge_group` triggers (2 workflow files)

`workflow.yml`:

```yaml
"on":
  pull_request:
    types: [opened, synchronize, reopened]
  merge_group:
  push:
    tags:
      - 'v*.*.*'
```

The FR-919 `changes` gate already short-circuits non-PR events to
`code == 'true'` (`github.event_name != 'pull_request' || …`), so merge
groups run the full matrix with zero job edits — correct, since a queue
group is the last validation before main.

`commitlint.yml` (exact shape per judgement R-3): keep job id
`commitlint` — branch protection names that context and no rename is
authorized. Change the job-level condition from
`github.event_name == 'pull_request'` to
`github.event_name == 'pull_request' || github.event_name == 'merge_group'`,
guard every step that reads `github.event.pull_request` (the
action-semantic-pull-request step) with
`if: github.event_name == 'pull_request'`, and add a merge-group-only
no-op step in the same job
(`if: github.event_name == 'merge_group'`, `run: echo "merge group —
title validated at PR time"`). Title validity was proven at PR time;
the group event only needs the context to report. RED-first YAML-shape
witnesses extend `tests/unit/test_commitlint_workflow.py`: both
workflows trigger on `merge_group`; the `commitlint` job runs for
`merge_group`; PR-title steps stay PR-only; the no-op lives in the same
`commitlint` job; `workflow.yml` still emits `test (3.11)` and
`test (3.13)` and runs the full matrix on merge groups (R-2 option 1).

### 2. Branch protection (exact contracts per judgement R-4)

Mutation — repository ruleset carrying the `merge_queue` rule (the API
surface that both accepts and returns every queue parameter):

```bash
gh api repos/sheikkinen/yamlgraph/rulesets -X POST --input - <<'JSON'
{"name": "merge-queue-main", "target": "branch", "enforcement": "active",
 "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
 "rules": [{"type": "merge_queue", "parameters": {
   "merge_method": "SQUASH", "grouping_strategy": "ALLGREEN",
   "min_entries_to_merge": 1, "max_entries_to_merge": 5,
   "max_entries_to_build": 5, "min_entries_to_merge_wait_minutes": 1,
   "check_response_timeout_minutes": 30}}]}
JSON
```

Strictness — `gh api -X PATCH
repos/sheikkinen/yamlgraph/branches/main/protection/required_status_checks
-F strict=false` (queue subsumes up-to-date; keeping both reintroduces
the pre-queue rebase requirement for no added safety).

Readback — `gh api repos/sheikkinen/yamlgraph/rulesets/<id>` must return
the `merge_queue` rule with every parameter above, and
`gh api repos/sheikkinen/yamlgraph/branches/main/protection` must show
`strict: false` with the three required contexts unchanged; both JSON
bodies are pasted into implementation notes. Parameter names are
verified against the live API schema at enforcement time; a mismatch is
recorded in the FR, not silently adapted.

Rollback — `gh api -X DELETE
repos/sheikkinen/yamlgraph/rulesets/<id>` plus `-X PATCH …
required_status_checks -F strict=true`, restoring the pre-queue regime.

Rollout order (frozen): (1) merge the tested workflow + documentation
changes under the current strict regime; (2) operator reviews both
workflow diffs and the exact settings payload; (3) apply the mutation
and strictness change in one controlled operation; (4) read back;
(5) only then enqueue witness PRs. If any required context fails to
report on the first merge group: stop, execute the rollback, return to
this FR — never `--admin` past the witness.

### 3. Ritual update (documentation)

`CLAUDE.md` branch-protection table and merge ritual: the merge verb
becomes plain `gh pr merge --squash` (auto-enqueues on a queue-required
branch per GitHub CLI docs). `--admin` is no longer the routine verb —
its prohibition is FR-935's scope, not this FR's.

## Acceptance Criteria

Superseded per judgement R-5: the revised acceptance criteria AC-01
through AC-13 in
[FR-934-merge-queue-on-main.judgement.md](FR-934-merge-queue-on-main.judgement.md)
govern enforcement verbatim — mechanically auditable witnesses (check
run URLs, settings readbacks, enqueue-time head SHAs, a named audit
source for the no-`--admin` proof, the R-2 policy assertion for the
docs-only witness, recorded operator review) plus changelog fragment,
diary reflection, and green `req_coverage --strict`.

## Alternatives Considered

| alternative | disposition |
|---|---|
| Auto-rebase bot / local watcher re-basing open PRs after each merge | REJECTED — rebuilds what the platform ships; still costs one full CI re-run per PR per landing; adds owned infrastructure (growth_as_default) |
| Serialize agents (one PR open at a time) | REJECTED — surrenders the concurrency FR-889 bought; the operator names parallel implementation as working today |
| Keep strict up-to-date, keep `--admin` bypass as the release valve | REJECTED — the toll stays for compliant merges and the bypass forfeits every required check; measured today: bypass is already the default verb |
| Batch merges manually (collect PRs, rebase once, merge in sequence) | REJECTED — same O(K²) CI in the worst case, adds human scheduling; the queue does exactly this mechanically with FIFO ejection |
| Merge queue (this FR) | PURSUED — free on public repos, subsumes strict up-to-date, squash-compatible, `gh pr merge` auto-enqueues non-interactively |

## Related

- [docs/plan-research-merge-queue.md](../docs/plan-research-merge-queue.md) — research record
- FR-889 (worktree → PR substrate; §4d deadlock cure, live and witnessed on PR #520)
- FR-919 (doc-only skip; its `changes` gate composes with merge_group unchanged)
- FR-935 (companion: deny `--admin` outside break-glass — the queue is only real if the bypass is exceptional)
- FR-902/FR-927 (cautionary precedent: automation aimed at the wrong end of the pipeline)
- docs/diary/diary-2026-08-30-the-parallel-writers-and-the-serial-door.md (the trap that fired this FR)

## Implementation record (2026-08-30)

**Phase 1 — workflow wiring (this PR, merged under the current strict regime per C-3):**

- RED commit 4955c651: `tests/unit/test_fr934_merge_queue_workflows.py` — 5
  witnesses failing for absent merge_group handling, 4 existing-truth pins
  passing (`@pytest.mark.req("REQ-YG-002")`).
- GREEN: `merge_group:` added to the `on:` blocks of `workflow.yml` and
  `commitlint.yml`. Commitlint job keeps id `commitlint`; job condition is
  `pull_request || merge_group`; `action-semantic-pull-request` and the
  feat-gate step guarded `pull_request`-only (the feat gate was accidentally
  null-safe on merge_group — explicit guard added per judgement AC-04);
  merge-group-only no-op step reports the required-context conclusion in the
  same job. `workflow.yml` needed no job changes: the `changes` gate's
  `event_name != 'pull_request'` short-circuit (FR-919 C-3) already routes
  merge groups to the full matrix — R-2 option 1 holds by construction.
- AC-11: CLAUDE.md branch-protection table rewritten to the post-queue truth;
  pinned by `TestClaudeMdMergeQueue` in `tests/unit/test_branch_protection_docs.py`
  (`REQ-YG-149`).
- AC-13: changelog fragment `changelog/unreleased/fr-934-merge-queue.md`,
  diary `docs/diary/diary-2026-08-30-the-queue-that-reports.md`.

**Phase 2 — pending (after this PR merges + operator reviews diffs and the
settings payload, C-2/AC-12):** ruleset POST + strict=false PATCH per §2,
readback into this record (AC-07), tested rollback (AC-08), then witness PRs
(AC-06, AC-09, AC-10).
