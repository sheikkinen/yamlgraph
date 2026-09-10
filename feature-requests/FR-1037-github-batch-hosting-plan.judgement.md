# Judgement: FR-1037 GitHub batch hosting architecture plan

**Verdict:** APPROVED WITH REVISIONS — the documentation-only direction is sound and appropriately conditional, but authority activates only after the FR makes the manual-dispatch permission boundary explicit and replaces its ambiguous verification criterion with named evidence and commands.

**Prior art:** FR-731, FR-819, FR-824, FR-826, FR-827, FR-862, FR-863, and FR-882 were considered by the independent judge; their disposition is recorded in the governing FR and the findings below.

**Provenance:** Independent Copilot judge via `scripts/judge.sh`, 2026-09-10,
model `gpt-5.6-sol`, session `90332cc7-a4bf-4e44-9fa5-c61c9ada864e`, input
commit `5d3846a9`. The sections below preserve the independent draft's verdict,
required revisions, frozen scope, acceptance criteria, conditions, and authority
statement. The descriptive findings are condensed; the full generated draft is
retained locally as `tmp/draft-judgement-copilot-FR-1037-github-batch-hosting-plan.md`.
**Human review:** On 2026-09-10 the operator reviewed the verdict and the two
folded revisions, then selected “Approve and proceed” for docs-only PR, outsider,
and merge. Application eligibility and access grants remain outside this approval.

## What is sound (condensed findings)

- **Single responsibility:** One reference, its governance artifacts, and one
  reflection preserve an architecture plan. The exclusions prevent application
  implementation, infrastructure changes, or changes to the reference application.
- **Consistency:** The workload remains unspecified and eligibility unresolved.
  Future delivery phases do not authorize execution, spending, or public release.
- **Research and prior art:** The committed evidence dispositions four options,
  including the workflow form alone and external execution. The cited prior FRs
  distinguish Actions execution, browser inference, issue runners, and product
  generators without treating any as provider-policy permission.
- **Feasibility:** Static Pages links to GitHub's workflow form; Actions owns
  execution and secrets remain outside browser code. The pinned deviant-daily
  revision supports the reusable execution and recovery patterns, not the new UI.
- **Security and operations:** Scoped permissions, visibility, retention, input
  validation, timeouts, bounded retries, concurrency, durable-state limitations,
  ambiguous effects, and preserving the last successful result are addressed.
- **Strategic classification:** Pattern documentation, not a new framework
  primitive or runtime use case. No new graph is warranted.
- **Testability:** Content assertions are observable; the two revisions below
  remove ambiguity in audience permissions and verification evidence.

## Required revisions

### R-1: State the permission boundary for the GitHub workflow form

Fold the manual-dispatch authorization requirement into the FR and reference. The current audience is only “personal use or a small trusted team” (`reference/github-batch-hosting.md:5`), while the interaction says a user signs in and confirms **Run workflow** (`reference/github-batch-hosting.md:54-57`) and later merely says to restrict execution to trusted repository users (`reference/github-batch-hosting.md:99-100`). “Trusted,” “signed in,” and “authorized to run the repository workflow” are not equivalent.

Revise the audience/handoff text to say that each initial user must have the repository permission GitHub requires to use the manual **Run workflow** control, and cite GitHub's official manual-run documentation for that requirement. State that users without that permission cannot use this handoff and that granting repository access is an operator decision outside this FR. Preserve the existing rule that the Pages link performs no dispatch and carries no token. Add this permission assertion to acceptance criteria.

### R-2: Replace AC5 with exact containment, documentation-check, and outsider evidence

AC5 currently requires “applicable documentation checks” and dispositioned outsider findings without naming a command or durable evidence location (`feature-requests/FR-1037-github-batch-hosting-plan.md:53`). That fails the rubric's requirement that every criterion identify a command, file, or assertion (`.github/skills/judge-fr/doctrine.md:43-44`) and makes a direct failing acceptance check impossible.

Fold the exact four paths into the FR: `feature-requests/FR-1037-github-batch-hosting-plan.md`, `feature-requests/FR-1037-github-batch-hosting-plan.judgement.md`, `reference/github-batch-hosting.md`, and `docs/diary/2026-09-10-reflection-fr-1037-hosting-is-not-permission.md`. Require `pre-commit run --files` with those four paths to pass. Require `scripts/outsider.sh <PR>` to run after the PR is opened and require its findings plus one disposition per finding to be preserved in a PR comment; “no findings” must be recorded explicitly. Use the merge-base diff command in AC-08 below as the path-containment witness.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-1037-github-batch-hosting-plan.md`, revised only to fold R-1 and R-2 and record judgement/implementation status |
| D-2 | `reference/github-batch-hosting.md`, including the architecture, evidence record, explicit manual-dispatch permission boundary, open eligibility gate, and future phases |
| D-3 | `feature-requests/FR-1037-github-batch-hosting-plan.judgement.md`, promoted from the human-reviewed draft |
| D-4 | `docs/diary/2026-09-10-reflection-fr-1037-hosting-is-not-permission.md` |
| D-5 | PR-hosted outsider output and per-finding dispositions; this is review evidence, not a fifth repository file |

Not authorized: application code; a frontend or Pages deployment; GitHub Actions workflows or configuration; YAMLGraph graphs or prompts; provider calls; secrets or permission changes; edits to deviant-daily; changes to CI, hooks, judge/review/authoring doctrine, or existing prior FRs; release or deployment activity; a claim that GitHub has approved the unspecified workload; a decision about the future workload, data visibility, spending limit, or repository access grant. Any implementation phase requires a separate researched and judged FR after the operator answers those questions.

## Revised acceptance criteria

- [ ] AC-01: `reference/github-batch-hosting.md` states in its opening recommendation that the workload is unspecified, Actions eligibility remains open, and merging the document authorizes no deployment, provider spend, or public-data release.
- [ ] AC-02: The reference identifies the audience as personal use or a small trusted team whose users possess the repository permission GitHub requires for manual workflow runs; it cites official GitHub manual-run documentation and states that granting repository access is outside this FR.
- [ ] AC-03: The architecture and prose state that Pages contains a link to GitHub's authenticated workflow form, that clicking the link does not dispatch a run, and that no shared GitHub or provider credential is present in browser code.
- [ ] AC-04: The reference pins deviant-daily revision `245b7387a79aba2ce9c7dc9d95025963f44e5e9b`, names the inspected `README.md` and `.github/workflows/_pipeline.yml`, distinguishes their implemented behavior from the proposed Pages dashboard, and does not treat that implementation as policy approval.
- [ ] AC-05: The reference has explicit sections or assertions covering scoped secrets and permissions, public/private result handling, input validation, timeouts, bounded retries, concurrency and pending-run behavior, artifact retention, last-successful-result preservation, ambiguous-effect recovery, and future phases.
- [ ] AC-06: The alternatives record contains four dispositioned solution classes, including workflow-form-only and external execution; the FR dispositions the cited prior art and explicitly records why no graph is needed.
- [ ] AC-07: `docs/diary/2026-09-10-reflection-fr-1037-hosting-is-not-permission.md` is committed and contains non-placeholder `**Trap:**`, `**Heuristic:**`, and `**Seed:**` entries.
- [ ] AC-08: `git diff --name-only "$(git merge-base HEAD origin/main)"...HEAD` prints exactly the four repository paths D-1 through D-4 and no code, graph, prompt, workflow, configuration, or additional documentation path.
- [ ] AC-09: `pre-commit run --files feature-requests/FR-1037-github-batch-hosting-plan.md feature-requests/FR-1037-github-batch-hosting-plan.judgement.md reference/github-batch-hosting.md docs/diary/2026-09-10-reflection-fr-1037-hosting-is-not-permission.md` exits zero.
- [ ] AC-10: After the PR is opened, `scripts/outsider.sh <PR>` is run and a PR comment records every outsider finding with a disposition, or explicitly records that there were no findings, before merge.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 and R-2 are folded into `feature-requests/FR-1037-github-batch-hosting-plan.md`. | GATE |
| C-2 | The implementation diff is limited to D-1 through D-4; PR comments may carry outsider evidence but no fifth repository file is authorized. | GATE |
| C-3 | Do not create or modify application code, graphs, prompts, workflows, CI, hooks, configuration, secrets, permissions, infrastructure, or deviant-daily artifacts under this FR. | GATE |
| C-4 | Do not represent billing eligibility, a prior working repository, or this judgement as GitHub approval for the unspecified workload. | GATE |
| C-5 | Future implementation remains blocked until a separate FR records the actual workload and the operator's answers to: Is the workload permitted on the selected GitHub services? Who receives repository access? Are outputs public or private? What provider and Actions spending limits apply? | GATE |
| C-6 | The promoted judgement remains advisory until human-reviewed; do not invoke or re-run the judge while folding this draft. | GATE |

Authority granted: after R-1 and R-2 are folded and the draft is human-reviewed, the enforcer may finalize only the four Markdown deliverables D-1 through D-4 and the PR-hosted outsider evidence within the frozen documentation scope.
