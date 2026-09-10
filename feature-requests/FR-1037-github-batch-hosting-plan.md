# Feature Request: FR-1037 GitHub batch hosting architecture plan

**Priority:** LOW
**Type:** Enhancement — documentation only
**Status:** Completed — documentation delivered in PR #650; application eligibility remains open
**Effort:** Small documentation change
**Requested:** 2026-09-10
**First consumer / first event:** An operator selecting hosting for a small batch tool, before building a frontend or provisioning execution.
**Research:** [Plan alternatives and inspected sources](../reference/github-batch-hosting.md#alternatives-and-research-record) — equivalent in-document evidence record; no new research pipeline is proposed.
**Prior art:** FR-826 (Enforced) and FR-862 (partially superseded by FR-863) supply the deviant-daily execution precedent; FR-863 concerns product-specific publishing constraints. FR-819 (Completed) supplies the GitHub-native digest pattern; FR-824 (Judged) applies it to a weekly bulletin; FR-827 (Enforced, witness gap recorded) builds an issue-driven runner. FR-731 (Judged) runs inference in the browser rather than Actions; FR-882 proposes a product-specific private generator. This document neither reopens nor changes these plans, and none establishes provider-policy approval for another workload. Search of hosting, Pages, and webpage-trigger plans found no rejected proposal being revived.

## Summary

Preserve the requested overall hosting plan as a standalone reference document.
This request authorizes documentation only, not application implementation.

## Value Statement

The operator can reuse a concrete architecture and see the authentication and
hosting-policy boundaries before spending effort on an unnecessary trigger service.

## Problem

The plan exists only in a chat. Its choices (trusted users and a GitHub UI handoff)
and limitations (unspecified workload and open hosting-policy gate) need a durable,
plain-language record. A working reference implementation is not evidence that
every similar workload is permitted by the hosting provider.

## Ideal Result

A successor reads one document and can distinguish the chosen architecture,
observed reference behavior, future implementation phases, and unresolved gates.

## Proposed Solution

Add `reference/github-batch-hosting.md` with the approved audience and handoff,
architecture, deviant-daily revision, secret/visibility boundaries, execution and
recovery contract, alternatives, costs, and a phased delivery plan. Cite official
GitHub documentation. Record a metacognitive diary entry with a Seed.

Scope is exactly the reference document, this FR, its independent judgement, and
one diary entry. No code, graph, workflow, configuration, release, deployment,
provider call, secret change, or modification to deviant-daily is authorized.
This is documentation of an architecture, not agent customization or a new
orchestration task; no new graph is needed.

## Acceptance Criteria

- [x] AC1: Reference records trusted-team audience with repository write access and GitHub-form handoff, explicitly distinguishing a link from direct dispatch; cites official manual-run permission requirements and leaves access grants to the operator.
- [x] AC2: Reference cites the inspected deviant-daily revision and distinguishes implemented behavior from the proposed dashboard.
- [x] AC3: Reference covers secrets, permissions, public/private results, retries, concurrency, retained output, and future phases without claiming deployment.
- [x] AC4: Reference front-loads the unresolved workload/hosting-policy gate and cites official terms; billing is not presented as eligibility.
- [x] AC5: The exact four-file diff and named pre-commit command below pass; the PR contains the posted outsider report and a comment dispositioning every finding (or explicitly recording no findings) before merge.
- [x] AC6: Committed diary includes trap, heuristic, and Seed.

### Exact verification contract (R-2)

`git diff --name-only "$(git merge-base HEAD origin/main)"...HEAD` must print
exactly these four paths and no others:

- `feature-requests/FR-1037-github-batch-hosting-plan.md`
- `feature-requests/FR-1037-github-batch-hosting-plan.judgement.md`
- `reference/github-batch-hosting.md`
- `docs/diary/2026-09-10-reflection-fr-1037-hosting-is-not-permission.md`

Run `pre-commit run --files feature-requests/FR-1037-github-batch-hosting-plan.md feature-requests/FR-1037-github-batch-hosting-plan.judgement.md reference/github-batch-hosting.md docs/diary/2026-09-10-reflection-fr-1037-hosting-is-not-permission.md`
and require exit zero. After opening the PR, run
`scripts/outsider.sh <PR> --comment` exactly once. Preserve its report and a
disposition per finding in PR comments; explicitly record when there are none.
The PR comments are the durable evidence, not a fifth repository file.

## Alternatives Considered

The [in-document research record](../reference/github-batch-hosting.md#alternatives-and-research-record)
dispositions four architecture options against inspected reference code and
official documentation. For this change, retaining the chat alone is rejected
because it loses discoverability; implementing the application now is rejected
because the user requested documentation and the actual workload is unspecified.
No claim of live deployment testing is made. Automated runtime tests are not
required because all four deliverables are prose, not executable artifacts.

## Decisions and implementation status

- 2026-09-10: Operator selected personal/small trusted team and accepted GitHub
  handoff initially. Requested isolated worktree, documentation PR, outsider, merge.
- Independent judgement: [APPROVED WITH REVISIONS](FR-1037-github-batch-hosting-plan.judgement.md).
- R-1 folded: reference explicitly requires repository write access and cites the
  manual-run documentation; granting access is outside scope.
- R-2 folded: exact path containment, pre-commit command, and durable outsider
  evidence requirements recorded above.
- 2026-09-10: Operator reviewed the judgement summary and chose “Approve and
  proceed” for the documentation-only PR, outsider, and merge.
- Verification: all four paths pass the named pre-commit command; editor diagnostics
  and diff whitespace checks are clean. The merge-base diff contains exactly D-1
  through D-4. Runtime tests are intentionally not applicable to this prose-only change.
- [PR #650](https://github.com/sheikkinen/yamlgraph/pull/650) preserves the outsider
  report (one run; derived NO, five terminology findings and four merge-evidence
  requests) and itemized dispositions. The description defines and links the terms;
  no rerun to obtain YES. Required CI must pass before the authorized merge.
- The application eligibility gate remains open and owned by its operator before
  any future implementation. Merging this documentation does not satisfy it.
