# Feature Request: FR-928 Cloud Judge — Run the Sole-Route Judge Graph in GitHub Actions

**Date:** 2026-08-30
**Type:** Process automation / CI
**Status:** Proposed (revised after first judgement REJECTED for missing research; R-1..R-5 folded)

**Research:** `feature-requests/FR-928.research.md` — sole-route research graph
run (brief: `feature-requests/research-briefs/fr-928-cloud-judge-problem-brief.md`,
provenance in `feature-requests/research-runs.jsonl`). Five personas, 5/5
`pursue`, convergent on ephemeral-cloud-runner execution (external-method ×3,
process-boundary ×2). `is_this_a_graph`: **no new graph** — the judge graph
exists and is the sole route; this FR adds a GitHub Actions host around the
unchanged `scripts/judge.sh` launcher. The librarian persona confirms Actions
is the invocation platform, not a graph engine. Additional alternatives
dispositioned in §5 below (kept disagreement: the A2A-based variants proposed
by two personas are rejected for this FR — heavier integration surface than
the Actions host, no added isolation).

**Prior art:** FR-827 (gitclaw forkable runner) is the direct basis — it proved
every load-bearing mechanism this FR reuses: a yamlgraph `copilot`-node graph
executed on an ubuntu-latest runner, `@github/copilot` CLI authenticated with a
dedicated read-only `COPILOT_CLI_TOKEN`, deterministic verify/publish steps
separated from the agent step, sha-pinned control bundle mirroring this repo's
`judge-fr` skill, and immutable input commits (witnessed live across FR-828..849
and intake run 32361594593). NC-415 built `scripts/judge.sh`, the operational
launcher this FR rehosts unchanged. NC-412/NC-414 fixed the judge graph as the
sole route with artifact-contract verification and the `JUDGE_EXECUTION`
re-entry sentinel — this FR adds a host, not a route. FR-889/FR-927 established
that main is OS-locked and lanes flow worktree→PR→squash; the cloud judge
publishes onto the FR's own PR branch, never main. The dormant chaplain
(`.chaplain/`) is precedent for automated plan→judge orchestration but is
explicitly NOT revived here. No REJECTED FR occupies this territory.

**First consumer / first event:** the next FR authored in any session lane. The
author pushes the FR PR; the judge workflow renders the draft judgement on a
cloud runner and commits it to the PR branch before the author's session has
finished its coffee — zero local judge latency, zero operator attendance.

## Ideal Result

An FR PR is opened; minutes later the same PR contains a
`feature-requests/FR-XXX-*.judgement.md` rendered by the sole-route judge graph
on an ephemeral cloud runner, with run-id provenance, and a PR comment stating
the verdict. The human decision point is unchanged and singular: merging the PR.
No judge run ever again occupies a local session, a local lock, or operator
attention. The local `scripts/judge.sh` route still works identically for
offline use.

## Problem

Operator calibration (diary 2026-08-30 "the gates nobody walks through"):
plan-judge output is never manually challenged — 900+ FRs conditioned trust —
yet every judge run costs an attended local session: venv PATH ritual, OS lock
serialization, 5–10 minutes of blocking latency in the authoring session, and
manual folding of `tmp/draft-judgement.md` into the `.judgement.md`. The judge
is already fully mechanized (a yamlgraph graph behind `scripts/judge.sh`); only
its *host* still consumes the scarcest resource. Doctrine also demands the
judge never run in the FR author's session — a fresh ephemeral runner satisfies
input closure by construction (FR content + repo doctrine are the only context
that exists on the runner).

## Proposed Solution

One new workflow, `.github/workflows/judge.yml`, modeled line-for-line on
gitclaw's `intake.yml`, reusing the existing sole route unchanged.

### 1. Triggers and deterministic guard (fail closed)

- `workflow_dispatch` with input `fr_path`. A deterministic validation step
  runs before any Copilot installation or secret exposure: the path must match
  `feature-requests/FR-[0-9]+-*.md`, contain no traversal, be a committed
  tracked file (`git ls-files --error-unmatch`), and not be a symlink — the
  cron.yml task-validation pattern verbatim. Invalid paths fail the job there.
- `pull_request` (types: opened, synchronize). The event only *starts* the
  workflow; a deterministic first job (`guard`) computes with `git diff
  --name-only base...head`: exactly one changed `feature-requests/FR-*.md`;
  no other changed FR files; sibling `.judgement.md` absent from the PR head
  tree; author association in `OWNER|MEMBER|COLLABORATOR`; head repo equals
  base repo (fork PRs unsupported — skip, never expose secrets). The agent job
  has `needs: guard` and runs only on its explicit pass output. No secret is
  readable before the guard passes; `pull_request_target` is not used.
- Concurrency group `judge-<fr-stem>`, `cancel-in-progress: false`.

### 2. Judge execution (agent step — read-only credentials)

- Job-level `permissions: contents: read` — nothing broader on the agent job.
- `actions/checkout` of the PR head, `persist-credentials: false`.
- Install runtime exactly as gitclaw intake: `npm install -g @github/copilot`,
  `pip install -e .` (source repo — judged graph and runtime at the same SHA).
- Authentication contract per FR-827's proven runner witness: the judge step
  receives `COPILOT_GITHUB_TOKEN: ${{ secrets.COPILOT_CLI_TOKEN }}` as step
  env — a dedicated Copilot-capable credential with **no repository write
  access**. No `gh auth login`; no stored credentials; the variable is scoped
  to the single `scripts/judge.sh` step and never exported to publish steps.
- Run `scripts/judge.sh <fr_path>` — unchanged. The OS lock is vestigial on an
  ephemeral runner but harmless; the `JUDGE_EXECUTION` sentinel and the
  artifact contract (non-empty `tmp/draft-judgement.md` with a `**Verdict:**`
  line) carry over verbatim.

### 3. Publish (deterministic step — `github.token` only)

Separate job, no LLM, explicit permissions `contents: write` +
`pull-requests: write` and nothing else. It copies `tmp/draft-judgement.md`
(passed as a job artifact) to `feature-requests/<fr-stem>.judgement.md`,
commits **that explicit path only** (`git add <path>` — no wildcard, no
`add -A`) with trailer `Judge-Run: <run_id>`, pushes to the PR branch, and
posts a PR comment containing only the verdict line plus links to the run and
the judgement commit. It does not inherit `COPILOT_CLI_TOKEN` or any gh auth
state; it must not modify the FR text, workflows, doctrine, or local-route
files. The *graph* still never commits or opens PRs — the workflow's
deterministic shell does, exactly as gitclaw's `executor_publish` separates
agent output from publication. On `workflow_dispatch` (no PR), upload the
draft as an Actions artifact instead.

### 4. Doctrine fit (no doctrine changes)

- Sole route preserved: same graph, same launcher, new host.
- "Never judge in the author's session": strengthened — the runner is nobody's
  session.
- "Advisory until human-reviewed": the judgement enters main only via the FR
  PR's squash merge — the merge IS the human review, the same C-2 pattern
  FR-927 used for its deletion diff.
- Input closure: the runner materially cannot see chat narrative.

### 5. Alternatives dispositioned (R-1, beyond the research table)

| Alternative | Disposition |
|---|---|
| Keep local-only judging | Rejected as sole mode — the witnessed attended cost is the problem; retained as supported fallback (AC-09/scope fence). |
| `workflow_dispatch` artifact-only (no publish) | Adopted as the dispatch-path behavior and Phase-1 witness; insufficient alone — the fold ritual survives. |
| PR-branch commit-back | Adopted — kills the manual fold; the squash merge remains the human gate (FR-927 C-2 pattern). |
| PR comment-only publication | Rejected — the judgement must be a committed file beside the FR (existing pairing gates); a comment is not a tracked artifact. Kept as the verdict summary channel. |
| GitHub App / PAT publication | Rejected — `github.token` with explicit job permissions suffices for same-repo PR branches; an App/PAT adds a standing credential with no added capability here. |
| Chaplain revival | Rejected for this FR — the whole-pipeline economics depend on this stage class first being proven off-host; explicitly fenced. |
| A2A-based delegation (research personas 1–2) | Rejected — heavier integration surface (SDK, agent card, endpoint) than the Actions host with no added isolation; preserved disagreement from the research run. |

## Scope Fence

- NO changes to `judge-fr/doctrine.md`, the judge graph, or the judge prompt.
- NO auto-merge of FR PRs (that is the separate auto-merge policy item).
- NO chaplain or inquisitor revival; NO enforce-in-cloud (separate FR — this is
  deliberately the smallest cloud rung: one stateless read-only stage).
- NO retirement of the local route; `scripts/judge.sh` local remains supported.
- NO new required status checks — the judge context is advisory.

## Acceptance Criteria

- [ ] AC-01: the FR carries a `**Research:**` field referencing the committed
  `feature-requests/FR-928.research.md` with an explicit `is_this_a_graph`
  answer (this revision).
- [ ] AC-02: the research record plus §5 disposition keep-local,
  dispatch-artifact-only, PR-branch commit-back, comment-only, GitHub App/PAT,
  and chaplain revival, with preserved disagreement (this revision).
- [ ] AC-03: `workflow_dispatch` with a valid `fr_path` under
  `feature-requests/FR-*.md` produces an Actions artifact containing a draft
  judgement with a `**Verdict:**` line rendered through unchanged
  `scripts/judge.sh`; invalid paths fail before Copilot
  installation/authentication.
- [ ] AC-04: on `pull_request` opened/synchronize, the deterministic pre-agent
  guard runs before secrets are exposed and permits only PRs whose diff changes
  exactly one `feature-requests/FR-*.md`, whose sibling `.judgement.md` is
  absent from the PR head, whose author association is OWNER/MEMBER/
  COLLABORATOR, and whose head repo equals the base repo (forks skipped).
- [ ] AC-05: a PR whose FR already has a sibling judgement exits before
  Copilot installation/authentication and publishes no duplicate judgement
  commit (guard witnessed).
- [ ] AC-06: the judge job has read-only repository permissions, checkout uses
  `persist-credentials: false`, and `COPILOT_GITHUB_TOKEN` (from
  `secrets.COPILOT_CLI_TOKEN`) is exposed only to the judge step; no
  write-capable token is readable by the LLM step.
- [ ] AC-07: the publish job has only `contents: write` +
  `pull-requests: write`, uses only `github.token`, does not inherit
  `COPILOT_CLI_TOKEN` or gh auth state, and commits with explicit git path
  arguments only.
- [ ] AC-08: the published `.judgement.md` commit carries `Judge-Run: <run_id>`
  provenance; the PR comment quotes only the verdict line plus links to the
  run and the judgement commit.
- [ ] AC-09: `scripts/judge.sh`, the judge graph, prompt, and doctrine are
  byte-identical before/after; any host-neutral launcher change returns to
  judgement with exact diff scope.
- [ ] AC-10: workflow-content tests assert the trust guard, changed-FR-count
  guard, sibling-judgement guard, concurrency group, permissions split,
  `persist-credentials: false`, and credential-environment separation.
- [ ] AC-11: a live same-repository PR witness records the run id, the
  judgement commit SHA, the PR comment URL, and non-secret evidence the
  credential boundaries were respected.
- [ ] AC-12: changelog fragment, FR implementation-status/decisions update, and
  diary reflection ship with the implementation PR.

## Risks

- Copilot CLI auth/entitlement on runners: mitigated — gitclaw runs this daily.
- Push to PR branch from workflow requires `contents: write` + explicit token
  push (gitclaw's freeze-input-commit pattern); forks are out of scope (single-
  maintainer repo).
- Model/latency variance in cloud: same graph, same model pin (`gpt-5.5`) as
  local; the artifact contract catches empty/malformed output.
- Runner minutes cost: one judge ≈ 10 min ubuntu-latest — noise next to the
  LLM token cost it replaces.
