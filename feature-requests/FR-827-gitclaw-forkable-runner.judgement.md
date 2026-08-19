# Judgement: FR-827 gitclaw — Forkable Issue-to-Feature Cron Runner

**Verdict:** APPROVED WITH REVISIONS — the forkable repo is a sound contrib/product artifact, but authority activates only after the FR fixes the invalid API fallback, makes graph authoring executable in forks, resolves the horoscope fixture contradiction, adds generated-diff containment, freezes the issue/cron state machines, and proves the fork path.

**Prior art:** FR-827 (the FR under judgement — this is its verdict). FR-823 hosted declarative graph runner: a hosted multi-tenant service; gitclaw is the inverse (adopter-owned fork, no hosting) — disjoint. FR-207 standalone scripture methodology repo: forkable-repo precedent for doctrine, not a runtime; gitclaw forks a runner, not a methodology — distinct territory. FR-820 stripe prepaid credits: false noun match via ".judgement" — unrelated.

**Reviewed against:** `feature-requests/FR-827-gitclaw-forkable-runner.md`; `feature-requests/FR-819-github-native-digest-poc-repo.md`; `feature-requests/FR-826-deviantart-daily-repo.md`; `feature-requests/FR-826-deviantart-daily-repo.judgement.md`; `capabilities/CAP-106-github-issues-remote-inbox.yaml`; `feature-requests/FR-081-copilot-node.md`; `feature-requests/FR-383-copilot-node-backend-api-fallback.md`; `feature-requests/105-copilot-session-continuations.md`; `docs/diary/diary-2026-08-19-the-satellite-mold-github-cron-yamlgraphs.md`; `examples/demos/horoscope/graph.yaml`; `examples/demos/horoscope/README.md`; `examples/demos/horoscope/prompts/horoscope.yaml`; `examples/demos/horoscope/prompts/assemble.yaml`; `examples/demos/horoscope/tools.py`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/skills/feature-request/SKILL.md`; `.github/skills/review-pr/doctrine.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`.

## What is sound

The first consumer and first event are concrete: a third-party fork processes an issue into a running YAMLGraph feature and a daily cron output (`feature-requests/FR-827-gitclaw-forkable-runner.md:9-15`). That satisfies the consumer test in the FR template and Scripture, which require naming who uses the proposal first and when (`feature-requests/TEMPLATE.md:8-10`; `.github/copilot-instructions.md:125-131`).

The strategic classification is **contrib/example / product repo**, not a framework primitive. FR-827 keeps yamlgraph core unchanged and composes existing node types (`feature-requests/FR-827-gitclaw-forkable-runner.md:222-225`), which aligns with FR-819's Actions-native satellite mold where the repo is runtime, state store, and publication channel (`feature-requests/FR-819-github-native-digest-poc-repo.md:17-22`) and with the diary's one-tree test: code, schedule, state, output, and audit fit one repo at daily cadence (`docs/diary/diary-2026-08-19-the-satellite-mold-github-cron-yamlgraphs.md:11-23`, `113-117`).

The prior-art disposition is directionally correct. CAP-106 is only remote intake into the local chaplain runtime (`capabilities/CAP-106-github-issues-remote-inbox.yaml:13-19`), while FR-827 proposes running the whole pipeline on Actions (`feature-requests/FR-827-gitclaw-forkable-runner.md:21-28`). FR-081 gives a first-class `copilot` node (`feature-requests/FR-081-copilot-node.md:28-31`), FR-105 gives session resumption for multi-step copilot workflows (`feature-requests/105-copilot-session-continuations.md:12-15`, `65-96`), and FR-383 gives a real API backend for reasoning-only fallback (`feature-requests/FR-383-copilot-node-backend-api-fallback.md:9-15`).

The trust-boundary instincts are good. FR-827 recognizes issue bodies as untrusted prompt input and gates execution to owner-authored or owner-labeled issues before any LLM call (`feature-requests/FR-827-gitclaw-forkable-runner.md:134-144`), matching the repo doctrine's instruction-boundary warning that vendor/model instructions are external input (`.github/copilot-instructions.md:81-85`).

## Required revisions

### R-1: Replace the invalid API fallback with a judged stop-or-redesign gate

Revise the Copilot CLI spike section so `backend: api` is not presented as "the backend is the only change" fallback for the full plan -> judge -> enforce -> review pipeline. FR-827 says the runner must spike Copilot CLI auth first and, if impossible, switch to `backend: api` with `ANTHROPIC_API_KEY` (`feature-requests/FR-827-gitclaw-forkable-runner.md:154-162`). But the same FR requires the enforce node to author files, run TDD, lint, and smoke (`feature-requests/FR-827-gitclaw-forkable-runner.md:117-120`), while FR-383 explicitly limits API mode away from CLI tool/session features (`feature-requests/FR-383-copilot-node-backend-api-fallback.md:54-58`) and defines API mode as `execute_prompt()` output wrapped in `CopilotResult` (`feature-requests/FR-383-copilot-node-backend-api-fallback.md:82-85`). Its linter also rejects API mode combined with CLI-only tool/session flags (`feature-requests/FR-383-copilot-node-backend-api-fallback.md:87-93`).

Fold this mechanically: AC-01 must say that if headless Copilot CLI auth fails, authority for the issue-to-feature runner stops. A revised FR may allow `backend: api` only for reasoning-only plan/judge/review nodes, and only if a separate, specified artifact-materialization mechanism replaces the agentic enforce step. That redesign must re-enter judgement because it changes the core architecture.

### R-2: Make graph authoring executable inside a fork, not merely doctrinal

Revise skills vendoring and enforce-stage design so generated `graph.yaml` and `prompts/*.yaml` artifacts have an executable authoring route in `gitclaw`. FR-827 says the repo vendors the four skill contracts as a snapshot (`feature-requests/FR-827-gitclaw-forkable-runner.md:175-181`) and that enforce authors feature graphs and prompts "per the graph-authoring skill" (`feature-requests/FR-827-gitclaw-forkable-runner.md:117-120`). But the graph-authoring doctrine's sole route is the executable adapter `scripts/author.sh <task-brief.md>` with a `tmp/draft-authoring-report.md` artifact, not doctrine text alone (`.github/skills/graph-authoring/doctrine.md:86-102`), and yamlgraph repo doctrine enforces the same adapter route for every material graph/prompt write (`.github/copilot-instructions.md:15`).

Fold this mechanically by choosing one route and specifying it in the FR: either vendor a gitclaw-local authoring adapter plus report verifier alongside the skill snapshot, or define a new gitclaw-local artifact report contract that is intentionally different and no longer claims compliance with the yamlgraph graph-authoring route. In either case, the FR must require lint and smoke evidence for every generated feature graph, and the generated report must be committed under the feature provenance directory.

### R-3: Resolve whether horoscope is pre-shipped or generated by the intake pipeline

Revise the acceptance fixture so the ideal result, layout, and ACs describe one consistent object. FR-827 says the repo ships with one canned acceptance feature, `features/horoscope/` (`feature-requests/FR-827-gitclaw-forkable-runner.md:46-47`, `92-95`), but the ideal result says the pipeline plans, judges, enforces, reviews, and commits `features/horoscope/graph.yaml` after the issue is filed (`feature-requests/FR-827-gitclaw-forkable-runner.md:51-56`), and AC-06 repeats that the pipeline commits `features/horoscope/` (`feature-requests/FR-827-gitclaw-forkable-runner.md:201-204`).

Fold this by choosing exactly one fixture model. Option A: pre-ship `features/horoscope/` as the cron-runner fixture, and use a different issue fixture to prove issue-to-feature generation. Option B: do not pre-ship `features/horoscope/`; ship only the issue template/request and require the pipeline to generate it. Update the repo tree, Ideal Result, AC-06, AC-07, and README walkthrough to match the chosen model.

### R-4: Add a generated-diff containment gate before push

Revise the trust boundary so owner labeling is not the only protection against prompt-injected repository mutation. FR-827 correctly treats issue bodies as untrusted and fences them before LLM use (`feature-requests/FR-827-gitclaw-forkable-runner.md:134-142`), but the generated agent has repository write access and the push node commits generated feature, output, state, and manifest changes (`feature-requests/FR-827-gitclaw-forkable-runner.md:125-128`). The FR constrains feature requests to graph/prompt/optional thin tools and rejects new secrets or external side effects only through the judge prompt (`feature-requests/FR-827-gitclaw-forkable-runner.md:232-235`), which is not a mechanical containment boundary. Repo doctrine treats model/vendor output modifying enforcement infrastructure as adversarial input (`.github/copilot-instructions.md:81-85`), and review doctrine requires human review gates for enforcement-infrastructure changes (`.github/skills/review-pr/doctrine.md:73-75`).

Fold this mechanically: before push, inspect the actual diff and fail closed unless every changed path is in the allowlist for the current run. Minimum allowlist: `features/<name>/**`, the per-feature provenance artifacts, the feature registry/manifest, `state/issues.jsonl`, and issue comment/ledger artifacts. Explicitly disallow `.github/workflows/**`, `.github/skills/**`, repository secrets configuration, package/dependency manifests, README policy changes, and any path outside the current feature unless a separate human-approved maintenance issue is being processed. The push step must use explicit path arguments, not broad `git add`, and ACs must include tests where a malicious issue tries to modify workflow/skills/secrets files and is rejected before commit.

### R-5: Freeze the intake and cron state machines at transition level

Revise the ledger design from "issue# -> status" and "failure commits a transition" into concrete states, resume behavior, and recovery rules. FR-827's layout names `state/issues.jsonl` as an idempotency ledger (`feature-requests/FR-827-gitclaw-forkable-runner.md:97-99`) and says failures commit transitions before exit so reruns resume (`feature-requests/FR-827-gitclaw-forkable-runner.md:131-132`), but it does not define the legal statuses, which transitions are committed before external side effects, or how interrupted plan/judge/enforce/review/push stages resume. FR-826's judged satellite precedent required exact statuses, committed transitions around external side effects, and `RECOVERY_REQUIRED` behavior where automatic retry could duplicate publication (`feature-requests/FR-826-deviantart-daily-repo.md:132-145`).

Fold this by adding two explicit state machines. Intake states must at least cover `seen`, `planned`, `judged_approved`, `judged_rejected`, `enforced`, `reviewed_approved`, `reviewed_rejected`, `pushed`, `closed`, and `failed_recovery_required`, with the commit point and rerun action for each state. Cron states must cover per-feature `running`, `succeeded`, `failed_recorded`, and "continue to next feature" behavior. Add tests for replay after successful close, failure before and after each external side effect, rejected judgement, rejected review, push failure, and poisoned cron feature.

### R-6: Prove the forkable path, not only the canonical repo path

Revise acceptance so the stated first consumer is witnessed. The FR's first consumer is a stranger's fork (`feature-requests/FR-827-gitclaw-forkable-runner.md:9-15`), and the README claims only two manual steps: fork plus PAT creation (`feature-requests/FR-827-gitclaw-forkable-runner.md:46-47`). Current ACs prove the canonical repo path (`feature-requests/FR-827-gitclaw-forkable-runner.md:201-206`) and use a "fresh-eyes read-through" for undocumented manual steps (`feature-requests/FR-827-gitclaw-forkable-runner.md:212-214`), but they do not require a fork/template-copy run. GitHub Actions fork behavior, workflow enablement, secret setup, and Copilot auth are exactly the product boundary.

Fold this by adding a fork witness: create a fresh fork or template-generated repo under a non-canonical name, configure only the documented secrets, file the documented issue, and record the Actions run IDs, commit SHA, closed issue link, and cron output. If GitHub requires an additional manual "enable workflows" step on fork/template creation, the README and Ideal Result must say so; do not hide it behind "fresh-eyes."

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-827-gitclaw-forkable-runner.md` folding R-1 through R-6 |
| D-2 | Separate public template repository `sheikkinen/gitclaw`, never vendored into yamlgraph |
| D-3 | `gitclaw.yaml`, prompts, thin tools, workflows, README, skills snapshot, state ledgers, feature registry, and tests inside the gitclaw repo |
| D-4 | Executable authoring route or explicitly renamed gitclaw-local artifact contract, with per-feature lint/smoke evidence |
| D-5 | One issue-to-feature witness, one cron witness, one rejected-judgement witness, one poisoned-feature cron witness, and one fork/template witness |
| D-6 | FR implementation-status update with non-secret run IDs, repo URL, snapshot SHA, scope deviations, and diary reflection |

Not authorized: yamlgraph core/runtime changes; changes to yamlgraph judge/review/authoring doctrine; changes to yamlgraph hooks or CI; Marketplace/GitHub App packaging; adding new YAMLGraph node types/providers; broad runner permissions beyond repo-scoped contents/issues/secrets actually required; auto-running generated features that request new secrets or external side effects beyond commit-back; committing the gitclaw repository as a nested repo, submodule, archive, or generated tree inside yamlgraph.

## Revised acceptance criteria

- [ ] AC-01: A headless-runner Copilot CLI spike completes before other implementation work: workflow log records install, auth method, one successful prompt, and non-secret evidence. If CLI auth fails, enforcement stops unless a revised FR is judged.
- [ ] AC-02: Public `sheikkinen/gitclaw` exists outside this repository, is marked as a template, and is not committed here as a nested repo, submodule, vendored directory, archive, or generated artifact.
- [ ] AC-03: The skills snapshot exists with `SNAPSHOT.md` recording yamlgraph source SHA and the exact vendored contract files; graph-authoring is backed by an executable gitclaw-local route/report contract, not only prose.
- [ ] AC-04: `gitclaw.yaml` passes `yamlgraph graph lint`; graph inspection proves judge and review start fresh sessions and enforce resumes the plan session only when CLI backend is active.
- [ ] AC-05: Intake trust gate runs before any LLM call: non-owner issue without owner-applied `gitclaw` label exits skipped, records no feature, and has a witnessed skipped Actions run.
- [ ] AC-06: Issue body is rendered only inside a fenced user-request block in copilot prompts; a prompt-injection fixture attempting to modify workflow/skills/secrets files is rejected by the diff containment gate before commit.
- [ ] AC-07: Intake ledger state machine is tested for replay after success and interruption before/after plan, judge, enforce, review, push, issue comment, and issue close; no replay starts a second independent pipeline for the same issue.
- [ ] AC-08: Rejected judgement path closes or comments on the issue with rationale, commits the rejection ledger transition, and registers no cron feature.
- [ ] AC-09: Rejected review path permits exactly one remediation lap back to enforce; the second rejected review fails closed with `review.md` posted or linked and no push of generated feature code.
- [ ] AC-10: Generated diff containment allowlist is enforced before push; push uses explicit path arguments and refuses `.github/workflows/**`, `.github/skills/**`, dependency manifests, secret configuration, and paths outside the current feature/provenance/state allowlist.
- [ ] AC-11: The horoscope fixture model is consistent: either pre-shipped horoscope proves cron and a separate issue proves feature generation, or horoscope is generated by the issue pipeline and not pre-shipped.
- [ ] AC-12: The issue-to-feature witness on the canonical repo records issue URL, Actions run ID, generated feature path, FR/judgement/review artifacts, commit SHA, issue close/comment link, and no secrets in committed/logged output.
- [ ] AC-13: Cron workflow runs all registered features, commits `outputs/<date>-<name>.md` for successes, writes structured failure records for failures, and continues past a poisoned feature fixture.
- [ ] AC-14: Fork/template witness proves the documented adopter path with only documented manual steps and records fork/template repo URL, run IDs, generated commit SHA, closed issue link, and cron output; README is corrected if any extra manual step is required.
- [ ] AC-15: README contains complete fork/template, Actions enablement if required, PAT/secret scopes, issue-label trust model, Copilot CLI/auth spike limitations, API-fallback limitations, and cron best-effort cadence.
- [ ] AC-16: Secret scan and run-log inspection prove no secret value appears in commits, outputs, issue comments, ledgers, workflow logs, or uploaded artifacts.
- [ ] AC-17: FR-827 records implementation status with repo URL, fork/template witness, run IDs, snapshot SHA, authoring reports, scope deviations, and diary entry.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-6 are folded into `feature-requests/FR-827-gitclaw-forkable-runner.md`. | GATE |
| C-2 | Do not invoke or re-run the judge while enforcing this FR. | GATE |
| C-3 | If headless Copilot CLI auth fails, stop; do not silently replace the agentic enforce path with `backend: api`. | GATE |
| C-4 | Any generated `graph.yaml` or `prompts/*.yaml` must have lint and smoke evidence from the executable authoring/report route chosen in the revised FR. | GATE |
| C-5 | The generated diff containment gate must run before every push and must fail closed on workflow, skills, secret, dependency, or out-of-feature path mutation. | GATE |
| C-6 | The new repo boundary is hard: do not vendor, submodule, archive, or commit gitclaw into yamlgraph. | GATE |
| C-7 | Any need for yamlgraph core changes, new node types, GitHub App/Marketplace packaging, or broader GitHub permissions requires a separate judged FR or explicit human review before use. | GATE |

Authority granted: after the required revisions are folded, enforcement may build the separate forkable `gitclaw` template repo and the directly necessary workflows, graph, prompts, tools, tests, skills snapshot, state ledgers, documentation, and witnesses within the frozen scope above.
