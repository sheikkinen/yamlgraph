# Judgement: FR-928 Cloud Judge - Run the Sole-Route Judge Graph in GitHub Actions

**Verdict:** APPROVED WITH REVISIONS -- the cloud-hosted judge direction is sound, but authority activates only after publication credentials are corrected so the judgement commit remains mergeable, and the guard/runtime/witness details are made mechanically testable.

**Prior art:** dispositioned in the FR and confirmed here — FR-827 (gitclaw runner) is the load-bearing feasibility precedent; NC-412/414/415 own the sole-route judge contract this FR rehosts unchanged; FR-890 supplies the research gate (satisfied by `feature-requests/FR-928.research.md`); FR-889/FR-927 fix the merge-boundary model the publication path relies on; the retired CAP-105 A2A surface is correctly rejected as heavier with no added isolation. No REJECTED FR occupies this territory.

**Reviewed against:** `feature-requests/FR-928-cloud-judge-github-actions.md`; `feature-requests/FR-928.research.md`; `feature-requests/research-briefs/fr-928-cloud-judge-problem-brief.md`; `feature-requests/research-runs.jsonl` (referenced but not otherwise needed); `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/skills/judge-fr/adapters/graph.yaml`; `.github/skills/judge-fr/adapters/README.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `feature-requests/TEMPLATE.md`; `scripts/judge.sh`; `capabilities/CAP-211-sole-route-judge-review.yaml`; `capabilities/CAP-105-a2a-consumer-phase2.yaml`; `capabilities/CAP-106-github-issues-remote-inbox.yaml`; `feature-requests/FR-827-gitclaw-forkable-runner.md`; `feature-requests/FR-927-retire-fr902-lane-guard-hooks.md`; `feature-requests/FR-927-retire-fr902-lane-guard-hooks.judgement.md`; `ARCHITECTURE.md`; `reference/getting-started.md`; `.github/workflows/workflow.yml`; `.github/workflows/weekly-recap.yml`; `.github/workflows/commitlint.yml`; `.github/workflows/security.yml`.

## What is sound

The problem is real and now has committed research. FR-928 points at `feature-requests/FR-928.research.md`, names the closed brief, records five personas, preserves disagreement, and answers `is_this_a_graph` as "no new graph" (`feature-requests/FR-928-cloud-judge-github-actions.md:7-17`). The research table contains five `pursue` candidates with distinct personas and the Actions/non-graph answer (`feature-requests/FR-928.research.md:3-13`). The brief supplies the cost witness: every judgement currently consumes interpreter setup, local lock time, 5-10 minutes of blocking latency, and manual folding, while doctrine forbids judging in the author's session (`feature-requests/research-briefs/fr-928-cloud-judge-problem-brief.md:13-24`). That satisfies the FR-890 research gate's demand for a committed record with substance, not just a field (`.github/skills/judge-fr/doctrine.md:118-128`; `feature-requests/TEMPLATE.md:11-20`).

The scope is minimal and correctly classified. FR-928 proposes one workflow around the existing launcher, not a new graph or new judge doctrine (`feature-requests/FR-928-cloud-judge-github-actions.md:62-65`, `feature-requests/FR-928-cloud-judge-github-actions.md:137-144`). The existing wrapper already exports `JUDGE_EXECUTION=1`, runs the judge adapter graph, and verifies `tmp/draft-judgement.md` by artifact contract rather than exit code (`scripts/judge.sh:54-60`); CAP-211 records the same sole-route wrapper contract and says the adapter graphs remain the sole execution routes (`capabilities/CAP-211-sole-route-judge-review.yaml:7-19`). Strategic classification: repo-local process automation / CI host for a governance stage, not a framework primitive. It is one concern: move the stateless judge stage off local attended sessions.

The architecture direction respects the instruction boundary. The FR puts deterministic guards before the LLM step (`feature-requests/FR-928-cloud-judge-github-actions.md:69-82`), gives the judge job read-only repository permissions and `persist-credentials: false` (`feature-requests/FR-928-cloud-judge-github-actions.md:84-98`), and separates publication into a non-LLM job (`feature-requests/FR-928-cloud-judge-github-actions.md:100-113`). That is the right response to repo doctrine treating agent output that touches enforcement infrastructure as adversarial input (`.github/copilot-instructions.md:82-86`) and judge doctrine requiring human review as a gate for CI/enforcement-infrastructure changes (`.github/skills/judge-fr/doctrine.md:94-103`). The graph itself still does not auto-fold, auto-commit, run CI, or merge; those prohibitions remain on the adapter (`.github/skills/judge-fr/adapters/README.md:19-30`), while FR-928 assigns deterministic shell publication outside the graph (`feature-requests/FR-928-cloud-judge-github-actions.md:110-113`).

The runner feasibility claim is precedented. FR-827 recorded a successful `ubuntu-latest` Copilot CLI spike: `npm install -g @github/copilot`, `COPILOT_GITHUB_TOKEN`/`COPILOT_CLI_TOKEN` authentication, an exact prompt round trip, and no API fallback (`feature-requests/FR-827-gitclaw-forkable-runner.md:254-273`). The judge adapter also really pins `gpt-5.5`, `allow_all_paths`, and `allow_all_tools`, which supports FR-928's model/contract claim (`.github/skills/judge-fr/adapters/graph.yaml:18-32`; `feature-requests/FR-928-cloud-judge-github-actions.md:196-197`).

Rejecting A2A for this FR is sound. Two research candidates proposed A2A, but the final FR deliberately chooses Actions as host and preserves A2A disagreement (`feature-requests/FR-928-cloud-judge-github-actions.md:15-17`, `feature-requests/FR-928-cloud-judge-github-actions.md:135`). CAP-105 is retired historical record, with its server/client/demo surface deleted (`capabilities/CAP-105-a2a-consumer-phase2.yaml:1-7`), so avoiding that integration surface is the smaller path.

## Required revisions

### R-1: Replace `github.token` PR-branch publication with a mergeable publish credential

Revise Proposed Solution §3, the GitHub App/PAT alternative row, AC-07, AC-08, AC-11, and Risks so the publish job uses a dedicated, human-provisioned write credential such as `JUDGE_PUBLISH_TOKEN` or a GitHub App installation token, scoped only to the current repository with contents-write and pull-requests-write capability. The credential must be available only in the deterministic publish job, never in the guard or judge jobs, and the judge job must still receive only the read-only Copilot credential.

Do not keep the current "github.token only" publication claim. FR-928 says the publish job uses only `github.token` and rejects a GitHub App/PAT because `github.token` "suffices" (`feature-requests/FR-928-cloud-judge-github-actions.md:102-108`, `feature-requests/FR-928-cloud-judge-github-actions.md:133`). Local precedent contradicts that for mergeability: the weekly recap workflow uses `RECAP_PAT` specifically because "PAT-created PRs trigger required checks; GITHUB_TOKEN PRs do not" (`.github/workflows/weekly-recap.yml:20-23`), while this repo's required CI contexts run on `pull_request` synchronize (`.github/workflows/workflow.yml:3-8`) and must report even for docs-only diffs (`.github/workflows/workflow.yml:61-66`; `CLAUDE.md:406-416`). A judgement commit pushed with only `GITHUB_TOKEN` risks becoming the latest PR SHA with no required contexts, turning the automation into a merge blocker.

### R-2: Specify exact guard checkout and diff mechanics

Amend the trigger/guard section and AC-10 to require deterministic checkout/fetch behavior for both `pull_request` and `workflow_dispatch`. The pull-request guard must compare the immutable event SHAs, not branch names: fetch or checkout enough history for `BASE_SHA...HEAD_SHA` to exist, run `git diff --name-only "$BASE_SHA...$HEAD_SHA"`, derive exactly one FR path from that diff, and check sibling judgement absence against the PR head tree. The workflow-dispatch path must checkout the dispatch ref, validate `fr_path` against the same `feature-requests/FR-[0-9]+-*.md` pattern, reject traversal and symlinks, and prove the path is tracked before any Copilot install or secret exposure.

FR-928 correctly names the intended guard but leaves the load-bearing checkout/fetch mechanics implicit (`feature-requests/FR-928-cloud-judge-github-actions.md:69-81`). Because the guard is the only thing between PR content and the Copilot credential, its exact SHA inputs and history availability must be testable, not entrusted to default `actions/checkout` behavior.

### R-3: Pin the runner runtime instead of inheriting `ubuntu-latest` defaults

Revise the judge job setup to pin Node and Python explicitly: use `actions/setup-node@v4` with Node 22 for `npm install -g @github/copilot`, use `actions/setup-python@v5` with Python 3.13, run `python -m pip install --upgrade pip`, and install with `python -m pip install -e .`. Add workflow-content assertions for these pins.

FR-928 currently says only to install `@github/copilot` and `pip install -e .` (`feature-requests/FR-928-cloud-judge-github-actions.md:88-89`). FR-827's successful runner witness depended on setup-node Node 22 (`feature-requests/FR-827-gitclaw-forkable-runner.md:254-260`), and this repo's current CI exercises Python 3.13 for the single-version core path (`.github/workflows/workflow.yml:43-52`). The cloud judge should not depend on moving `ubuntu-latest` interpreter defaults.

### R-4: Make the live witness evidence concrete and non-secret

Rewrite AC-11 so the implementation record must include exact non-secret evidence fields: PR number, judge workflow run URL/id, publish job URL/id, judgement commit SHA, PR comment URL, commit author, the credential name used by the publish step (name only, never value), and a workflow-content/test citation proving `COPILOT_CLI_TOKEN` is absent from publish-job env while the publish credential is absent from guard and judge job env. Keep the current requirement that no token values, OAuth output, or full environment dumps appear in logs, artifacts, comments, or committed files.

The current AC-11 asks for "non-secret evidence the credential boundaries were respected" but does not define what evidence satisfies it (`feature-requests/FR-928-cloud-judge-github-actions.md:184-186`). That is too aspirational for a credential-boundary FR. The enforcer needs a fixed witness shape.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-928-cloud-judge-github-actions.md`: fold R-1 through R-4, update status, and later record implementation status, decisions, live witness facts, and deviations. |
| D-2 | `.github/workflows/judge.yml`: new advisory judge workflow with `workflow_dispatch` and guarded same-repo `pull_request` triggers. |
| D-3 | Workflow-content tests under the existing test suite: assert trigger shape, trust guard, exact SHA diff guard, sibling-judgement guard, same-repo/author-association fence, concurrency group, permissions split, `persist-credentials: false`, runtime pins, explicit-path publication, and credential-environment separation. |
| D-4 | Publish-step shell inside `.github/workflows/judge.yml`: copy only `tmp/draft-judgement.md` to the sibling judgement path, `git add` that explicit path only, commit with `Judge-Run: <run_id>`, push with the dedicated publish credential, and post a verdict-only PR comment. |
| D-5 | `changelog/unreleased/*.md`: process/CI fragment for FR-928. |
| D-6 | `docs/diary/*.md`: metacognitive reflection for the cloud-judge enforcement work. |

Not authorized: changing `.github/skills/judge-fr/doctrine.md`, the judge prompt, the judge adapter graph, or `scripts/judge.sh`; creating a second judge route; invoking the judge outside `scripts/judge.sh`; using `pull_request_target`; exposing any repository-write credential to the LLM/judge step; supporting fork PRs; auto-merging FR PRs; adding a required status check for the judge workflow; reviving chaplain/inquisitor; moving enforce/review/authoring into cloud; retiring local judgement; modifying branch protection; changing unrelated workflows beyond tests/docs that directly exercise the new workflow.

## Revised acceptance criteria

- [ ] AC-01: FR-928 contains a `**Research:**` field pointing at committed `feature-requests/FR-928.research.md`; that record names its brief, run date, personas, preserved disagreement, and an explicit `is_this_a_graph` answer.
- [ ] AC-02: FR-928 dispositions keep-local, dispatch-artifact-only, PR-branch commit-back, comment-only publication, GitHub App/PAT publication, chaplain revival, and A2A delegation; after R-1, the GitHub App/PAT row selects the dedicated publish credential required for mergeable commit-back rather than rejecting it.
- [ ] AC-03: `.github/workflows/judge.yml` defines `workflow_dispatch` with `fr_path`; the dispatch path validates `feature-requests/FR-[0-9]+-*.md`, rejects traversal and symlinks, proves the file is tracked, and fails before Copilot installation/authentication on invalid input.
- [ ] AC-04: `.github/workflows/judge.yml` defines `pull_request` on opened/synchronize with a deterministic guard job that fetches/checks out the exact base/head SHAs, permits only same-repository PRs from OWNER/MEMBER/COLLABORATOR authors, computes `git diff --name-only "$BASE_SHA...$HEAD_SHA"`, derives exactly one changed `feature-requests/FR-*.md`, rejects any other changed FR/judgement files, and proves the sibling `.judgement.md` is absent from the PR head tree.
- [ ] AC-05: A PR whose FR already has a sibling judgement exits before Copilot installation/authentication and publishes no duplicate judgement commit; this skip path is covered by workflow-content tests.
- [ ] AC-06: The judge job has `permissions: contents: read`, checks out the PR head with `persist-credentials: false`, installs pinned Node 22 and Python 3.13, runs `npm install -g @github/copilot`, runs `python -m pip install --upgrade pip` and `python -m pip install -e .`, and exposes `COPILOT_GITHUB_TOKEN: ${{ secrets.COPILOT_CLI_TOKEN }}` only to the `scripts/judge.sh <fr_path>` step.
- [ ] AC-07: The publish job has only contents-write and pull-requests-write capability, uses the dedicated publish credential from R-1 only in deterministic checkout/push/comment steps, does not inherit `COPILOT_CLI_TOKEN` or any judge-step auth state, and commits with explicit git path arguments only.
- [ ] AC-08: The published `.judgement.md` commit carries `Judge-Run: <run_id>` provenance; the PR comment quotes only the verdict line plus links to the run and judgement commit; no token values, OAuth output, or environment dumps appear in logs, artifacts, comments, or committed files.
- [ ] AC-09: `scripts/judge.sh`, `.github/skills/judge-fr/adapters/graph.yaml`, the judge prompt, and judge doctrine are byte-identical before/after; any host-neutral launcher or adapter change must return to judgement with exact diff scope.
- [ ] AC-10: Workflow-content tests assert the trust guard, exact-SHA diff guard, changed-FR-count guard, sibling-judgement guard, concurrency group `judge-<fr-stem>` with `cancel-in-progress: false`, permissions split, `persist-credentials: false`, runtime pins, and credential-environment separation.
- [ ] AC-11: A live same-repository PR witness records PR number, judge workflow run URL/id, publish job URL/id, judgement commit SHA, PR comment URL, commit author, publish credential name (name only), and the workflow-content/test citation proving credential separation.
- [ ] AC-12: A changelog fragment, FR implementation-status/decisions update, and diary reflection ship with the implementation PR.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is not active until R-1 through R-4 are folded into FR-928. | GATE |
| C-2 | The judge/LLM job must never receive a repository-write credential; write-capable credentials may exist only in deterministic non-LLM publish steps after the guard and judge artifacts exist. | GATE |
| C-3 | Do not use `pull_request_target` or support fork PRs in this FR. | GATE |
| C-4 | Do not change the judge doctrine, prompt, adapter graph, or `scripts/judge.sh`; host-only workflow automation is the authorized surface. | GATE |
| C-5 | A human must review the new CI workflow and credential-boundary diff before the workflow is treated as operational, because CI/enforcement-infrastructure changes are adversarial input under judge doctrine. | GATE |
| C-6 | If the dedicated publish credential cannot be provisioned or cannot trigger required checks on the judgement commit, stop and return to judgement; do not silently fall back to `GITHUB_TOKEN` commit-back. | GATE |

Authority granted: after the required revisions are folded, enforcement may add an advisory GitHub Actions host for the existing sole-route judge graph, with guarded read-only judge execution and deterministic PR-branch publication through a mergeable, publish-only credential.
