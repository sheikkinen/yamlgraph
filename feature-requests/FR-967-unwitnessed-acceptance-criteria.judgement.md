# Judgement: FR-967 witness FR-962's shipped behaviour and block unwitnessed acceptance criteria at merge

**Verdict:** SPLIT — the retrospective FR-962 witness repair and the repository-wide merge policy are independently valuable, independently testable concerns; neither receives implementation authority until it is specified and judged as its own FR.

**Prior art:** [FR-967-unwitnessed-acceptance-criteria.md](FR-967-unwitnessed-acceptance-criteria.md) — the subject of this judgement; its own `**Prior art:**` line dispositions CAP-116, FR-851, FR-206 and FR-145, the four mechanisms that each passed on FR-962. [FR-636-demo-coverage-gate.md](FR-636-demo-coverage-gate.md) [Judged — APPROVED, scope reduced] — the nearest real neighbour, and not a vocabulary collision: it is also a coverage gate. Distinguished by subject — FR-636 proves `yamlgraph/` **framework modules** are reachable by running curated demos under `coverage.py`, detecting dead core code; it reads module coverage, never an FR document, and would report nothing about an unchecked acceptance criterion. The two gates are complementary and share no code. [FR-800-memory-demo-mock-seam-correction.md](FR-800-memory-demo-mock-seam-correction.md) [Enforced] and [FR-777-shared-shell-toolbelt-manifests.md](FR-777-shared-shell-toolbelt-manifests.md) [Enforced] — matched on "acceptance" in ordinary usage; mock-seam correction and shell toolbelt manifests respectively, neither touching criterion disposition. [FR-520-dm-v2-chapter-lived-positional-working-memory.md](FR-520-dm-v2-chapter-lived-positional-working-memory.md) — dungeon-master working memory; a vocabulary collision.

**Reviewed against:** `feature-requests/FR-967-unwitnessed-acceptance-criteria.md`; `feature-requests/FR-967.research.md`; `feature-requests/FR-962-person-profile-census-authored-prs.md`; `feature-requests/FR-962-person-profile-census-authored-prs.judgement.md`; `feature-requests/FR-966-visibility-conjunction-unsatisfiable.md`; `feature-requests/FR-851-requirement-witness-audit.md`; `feature-requests/FR-206-demo-proof-gate.md`; `feature-requests/FR-145-phantom-requirement-detection.md`; `capabilities/CAP-116-acceptance-tests-before-enforce.yaml`; `.github/workflows/commitlint.yml`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The incident is concrete rather than hypothetical: FR-962 still records unchecked criteria, including explicit test obligations (`feature-requests/FR-962-person-profile-census-authored-prs.md:328-344`), and FR-967 identifies a specific downstream defect and false evidence claims (`feature-requests/FR-967-unwitnessed-acceptance-criteria.md:28-56`). The proposed fixture-driven tests are appropriately deterministic, keep GitHub and LLM calls outside the unit boundary, and target the seams named by FR-962 (`feature-requests/FR-967-unwitnessed-acceptance-criteria.md:70-82,104-113`).

The research record is substantive: five personas ran, disagreement was preserved, precedent was named, and `is_this_a_graph` was answered (`feature-requests/FR-967.research.md:5,14-20`). A deterministic CI policy is the correct implementation class, and placing a policy at the merge boundary follows repository doctrine (`.github/copilot-instructions.md:152`). Creating a separate FR for CI also respects FR-962's frozen exclusion of hooks and CI (`feature-requests/FR-962-person-profile-census-authored-prs.judgement.md:65-78`).

| Rubric criterion | Finding |
|---|---|
| Scope | The two proposed deliverables are each clear, but their bundle is not minimal: tests that retire one historical feature's debt do not require a repository-wide gate, and the gate does not require those feature-specific tests (`feature-requests/FR-967-unwitnessed-acceptance-criteria.md:68-91`). |
| Consistency | The title, summary, value statement, and ideal promise witnessed criteria, but D-2 expressly checks only state and admits that a falsely checked box passes (`feature-requests/FR-967-unwitnessed-acceptance-criteria.md:15-26,59-65,92-95`). |
| Measurability | D-1's named fixtures and most gate exit-code cases are mechanical (`feature-requests/FR-967-unwitnessed-acceptance-criteria.md:104-124`), but “adjacent” deferral syntax and title/file resolution are not frozen. |
| Feasibility | Python parsing and CI wiring fit existing infrastructure, but the claimed existing title convention covers only `feat` PRs, while FR-967 is a Bug and existing `fix` jobs do not require an FR ID (`.github/workflows/commitlint.yml:52-59,169-170,306-322`). |
| Architecture alignment | Deterministic policy at CI and ADR-001 markers align with existing patterns (`.github/copilot-instructions.md:167-168`); a state-only checkbox gate conflicts with the doctrine against shape-without-substance gates (`.github/copilot-instructions.md:79`). |
| Single responsibility | D-1 is historical acceptance-test debt; D-2 is prospective repository governance. The judge doctrine requires such bundles to split (`.github/skills/judge-fr/doctrine.md:50`). |
| Strategic classification | D-1 is a contrib/example repair for one shipped demo. D-2 is a repository process primitive applying to future FR-linked PRs. They have different consumers, blast radii, and review requirements. |
| Testability | Direct failing tests can be derived for D-1 and the parser's basic states, but no test can prove the stated “witness” property from D-2 because D-2 defines no checkbox-to-test relation. The research candidates did define such cross-references (`feature-requests/FR-967.research.md:16-18`). |

## Required revisions

### R-1: Extract the FR-962 witness repair

Create a child FR limited to the FR-962 acceptance-test debt. Preserve the two named unit-test files, offline fixtures, ten explicitly mapped FR-962 criteria, disposition of all seventeen FR-962 criteria, ADR-001 wiring, changelog, and diary. Exclude `scripts/ac_witness_gate.py`, workflow changes, title parsing, and general acceptance-criterion policy.

The child must state whether its tests characterize current behavior or enforce FR-962's frozen contract. If they enforce the contract, authorize only the production corrections needed to make those named witnesses pass and enumerate those production surfaces. Do not use `**Deferred:**` to convert a failing frozen requirement into success.

### R-2: Extract the merge-boundary policy

Create a separate child FR limited to the deterministic acceptance-criterion policy, its parser tests, CI integration, CAP/REQ wiring, changelog, and diary. Exclude all person-profile census tests, fixtures, implementation changes, proof repair, and edits that disposition FR-962's criteria.

This child must re-enter research and judgement as enforcement infrastructure. Its acceptance criteria must include explicit human review before merge, as required for CI changes (`.github/skills/judge-fr/doctrine.md:98`; `feature-requests/FR-962-person-profile-census-authored-prs.judgement.md:112`).

### R-3: Choose truth enforcement or honest state enforcement

Resolve the D-2 contradiction in the policy child:

1. **Recommended — witness enforcement:** define a deterministic, machine-checkable relation from every checked criterion to committed test evidence, then fail when that evidence is absent; or
2. **State enforcement:** rename the feature to an acceptance-criterion disposition gate and narrow every claim to checked/deferred bookkeeping. It must not claim that checked criteria are witnessed or true.

The current hybrid is forbidden: admitting that a false check passes (`feature-requests/FR-967-unwitnessed-acceptance-criteria.md:92-95`) while promising that merge cannot contain unwitnessed claims (`feature-requests/FR-967-unwitnessed-acceptance-criteria.md:15-26`) reproduces `gate_checks_shape_not_substance`.

### R-4: Freeze the policy grammar and applicability

In the policy child, specify mechanically:

- which PR types must carry an FR ID and which merely trigger the gate when one is present;
- behavior for zero, one, and multiple FR IDs in a title;
- exact and unique FR-file resolution, including missing and ambiguous matches;
- the acceptance-criteria section boundary and checkbox syntax;
- the exact association rule for `**Deferred:** <reason>`, including minimum non-whitespace substance;
- handling of deleted/renamed FR files and non-FR markdown checkboxes;
- pull-request and merge-queue behavior so every required status context reaches a conclusion.

Do not call FR-ID extraction an existing `fix` convention: the current workflow mandates an FR reference only for `feat` (`.github/workflows/commitlint.yml:52-59`).

### R-5: Give each child its own consumer and success boundary

The repair child's first consumer is the maintainer enforcing FR-966 who needs trustworthy FR-962 fixtures. The policy child's first consumer is the reviewer of the first in-scope FR-linked PR containing an invalid criterion disposition. Each child must have its own Ideal Result, alternatives, acceptance criteria, effort, and explicit exclusions.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | A new child FR for FR-962 witness debt: person-profile census unit fixtures/tests, exact criterion disposition, and only enumerated corrections required by those tests |
| D-2 | A new child FR for prospective merge policy: deterministic parser, parser fixtures/tests, CI workflow integration, and policy-specific CAP/REQ documentation |

Not authorized: implementation under FR-967 as currently bundled; edits to judge/review doctrine; Chaplain runtime changes; generic markdown parsing infrastructure; LLM-based acceptance evaluation; changes to unrelated census graphs, prompts, adapters, or demos; treating a checkbox alone as proof of a test witness; silently exempting `fix` PRs, merge-queue runs, missing FR files, ambiguous FR IDs, or malformed deferrals.

## Revised acceptance criteria

- [ ] AC-01: Two child FR files exist, one containing only the FR-962 witness repair and one containing only the prospective merge policy; each references FR-967 as its split parent.
- [ ] AC-02: The repair child maps every FR-962 criterion to exactly one of: a named committed test witness, a concrete production correction plus named test witness, or a reasoned deferral that does not claim success.
- [ ] AC-03: The repair child contains no CI, hook, title-parser, or repository-wide policy deliverable.
- [ ] AC-04: The policy child contains no person-profile census implementation, test-debt repair, proof regeneration, or FR-962 criterion-disposition deliverable.
- [ ] AC-05: The policy child makes the R-3 choice explicit and uses “witness” only if a deterministic criterion-to-test relation is specified and tested.
- [ ] AC-06: The policy child freezes every applicability and grammar case in R-4 as a fixture-backed assertion with expected exit status and diagnostic.
- [ ] AC-07: The policy child includes a CI test or workflow witness for both `pull_request` and `merge_group` events, with no required context left pending or skipped without a conclusion.
- [ ] AC-08: Each child has a committed, substantive research record, its own first consumer/event, and a separate judgement before enforcement.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No production or CI implementation begins under this SPLIT verdict; each child re-enters plan → judge independently. | GATE |
| C-2 | D-1 may not expand from FR-962 witness debt into general census redesign or use deferral to hide a failing frozen contract. | GATE |
| C-3 | D-2 may not claim witness truth unless its deterministic evidence relation is frozen and directly tested. | GATE |
| C-4 | A human must review and accept the policy semantics and CI blast radius before D-2 merges. | GATE |
| C-5 | Both children must preserve input closure and independently disposition their retrieved prior art, including this split judgement. | GATE |

**Question for the human:** For the D-2 child, choose **A — witness enforcement** (recommended because it matches the title, value statement, research convergence, and incident) or **B — state-only disposition enforcement** (smaller, but must be named and described honestly). Evidence: `feature-requests/FR-967.research.md:16-20` recommends test-backed gates, while the present proposal deliberately weakens that to checkbox state at `feature-requests/FR-967-unwitnessed-acceptance-criteria.md:92-95`.

Authority granted: none; authority can be granted only by separate judgements of the two revised child FRs.
