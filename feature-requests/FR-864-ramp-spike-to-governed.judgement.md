# Judgement: FR-864 Ramp - Bootstrapping a Repo from Spike to Governed

**Verdict:** SPLIT - the need is real and the graph-shaped direction is sound, but the FR bundles reusable ramp tooling, target-repo application, graph authoring, and external-repo retirement into one enforcement surface; no implementation authority activates until the concerns below re-enter as separate judged FRs.

**Reviewed against:** `feature-requests/FR-864-ramp-spike-to-governed.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `feature-requests/FR-207-standalone-scripture-methodology-repo.md`; `feature-requests/FR-748-fr-atlas-onboarding-summary.md`; `examples/demos/fr-atlas/graph.yaml`; `feature-requests/FR-826-deviantart-daily-repo.md`; `feature-requests/FR-826-deviantart-daily-repo.judgement.md`; `feature-requests/FR-862-deviant-daily-on-demand-publish.md`; `feature-requests/FR-862-deviant-daily-on-demand-publish.judgement.md`; `feature-requests/FR-863-deviant-daily-publish-policy-boundary-mirroring.md`; `docs/diary/diary-2026-08-23-the-spike-ends-at-a-commit.md`; `docs/diary/diary-2026-08-23-process-transfers-by-practice.md`; `docs/diary/diary-2026-08-23-nothing-announces-the-absent-guard.md`. No author chat narrative was consumed.

**Prior art:** dispositioned in "What is sound" below — FR-207 (the superseded template mechanism, diagnosed not repeated), FR-748/`fr_atlas` (corpus map + merge + reconciliation precedent, reused), FR-826/FR-862/FR-863 (target-repo history and the incident corpus). FR-858 is the nearest retirement-FR precedent for child D. Each child FR must re-disposition these for its own territory (AC-06); irrelevant prior art is to be marked non-overlap, not inherited wholesale. No REJECTED prior art occupies this territory. FR-864 is the subject FR.

## What is sound

The first consumer and first event are concrete. FR-864 names `sheikkinen/deviant-daily` and the first command `scripts/ramp.sh ~/Documents/src/deviant-daily --tier 2`, after a live repo had no hooks, no CI running its tests, no doctrine file, and four production failures in two hours (`feature-requests/FR-864-ramp-spike-to-governed.md:8-13`). The cited diary record supports the production-transition claim with the first public publish and cron-enabling commits (`docs/diary/diary-2026-08-23-the-spike-ends-at-a-commit.md:22-28`) and supports the absent-enforcement claim with the workspace-vs-repo hook distinction and empty repo hooks (`docs/diary/diary-2026-08-23-nothing-announces-the-absent-guard.md:18-27`).

The prior-art diagnosis is directionally sound. FR-207 really was a template-repo extraction of governance assets (`feature-requests/FR-207-standalone-scripture-methodology-repo.md:48-65`) with a `scripture.yaml`/`render.sh` substitution mechanism (`feature-requests/FR-207-standalone-scripture-methodology-repo.md:108-142`). The diary evidence records why that mechanism decayed: `scripture-dev` was a distributor that did not consume its own process, while `customer-service-agent-platform` practiced the process and developed live artifacts (`docs/diary/diary-2026-08-23-process-transfers-by-practice.md:11-27`, `49-52`).

The decision to make the target-specific judgement steps graphs rather than scripts aligns with repo doctrine and precedent. The Scripture says N-items-times-LLM-call / map-reduce work should look for the graph shape before scripts or subagents (`.github/copilot-instructions.md:133`), and FR-748 is a proven corpus map + merge + mechanical coverage pattern: chunk map, merge, and code-side count-in == count-out reconciliation (`feature-requests/FR-748-fr-atlas-onboarding-summary.md:62-80`; `examples/demos/fr-atlas/graph.yaml:59-73`, `88-104`).

The FR correctly excludes the spike detector and absent-enforcement warning from this proposal (`feature-requests/FR-864-ramp-spike-to-governed.md:61-62`, `204-208`). Those would change enforcement infrastructure and deserve their own judgement; the judge doctrine treats enforcement-infrastructure changes as adversarial input requiring explicit gate conditions (`.github/skills/judge-fr/doctrine.md:96-101`).

Strategic classification: **Contrib/example / governance tooling**, not a YAMLGraph framework primitive. The FR has one urgent concrete consumer and a plausible repeatable pattern, but it adds repo-governance assets, scripts, and demos around existing YAMLGraph graph/runtime primitives rather than changing YAMLGraph core semantics.

## Required revisions

### R-1: Split the reusable ramp installer from target-repo enforcement

Create a child FR for the generic ramp installer and asset manifest only. Its scope may include `scripts/ramp.sh`, a source asset inventory, tier definitions, idempotent copy/no-overwrite behavior, dry-run behavior, and tests against scratch repos. It must not apply the ramp to `deviant-daily`, author LLM graphs, produce RTM content, archive `scripture-dev`, or modify any sibling repo.

This split is required because FR-864 defines a reusable installer (`feature-requests/FR-864-ramp-spike-to-governed.md:83-90`), four graph pipelines (`feature-requests/FR-864-ramp-spike-to-governed.md:106-121`), a concrete target ramp witness (`feature-requests/FR-864-ramp-spike-to-governed.md:176-178`), and `scripture-dev` archival (`feature-requests/FR-864-ramp-spike-to-governed.md:138-144`, `179-180`) in one enforcement pass. That violates the judge rubric's single-responsibility rule: bundles get split (`.github/skills/judge-fr/doctrine.md:49-58`).

### R-2: Split target-tailoring graphs from mechanical copy work

Create a child FR for target-tailoring graph artifacts. It may cover `ramp_doctrine`, `ramp_rtm`, and `ramp_incidents` if the FR proves they share one runtime contract: target inventory in, draft artifacts out, human review before landing, and mechanical reconciliation where applicable. It must specify exact graph paths, prompt paths, draft output paths, schemas, validation commands, and smoke inputs. Any `graph.yaml` or `prompts/*.yaml` creation or material modification must use the graph-authoring route and retain the authoring report, because repo doctrine makes artifact class the trigger (`.github/copilot-instructions.md:15`).

The child FR must not include `salvage_classify` unless it is explicitly scoped as a target-tailoring graph for a target repo. As written, `salvage_classify` classifies a different source repo's assets for retirement (`feature-requests/FR-864-ramp-spike-to-governed.md:117-118`, `138-144`), which is a separate concern from tailoring doctrine, RTM, and incidents for the target repo.

### R-3: Split `scripture-dev` salvage and retirement into its own FR

Create a child FR for `scripture-dev` salvage/retirement. It must enumerate the exact input repository/ref to be classified, the 27 artifacts counted, the disposition output format, the lift process into yamlgraph ramp assets, and the human authorization required before GitHub archive state is changed. Archiving another repository is an administrative action and must not be hidden as an acceptance criterion inside a ramp-tooling FR.

The current FR's prior-art section says FR-207 is superseded and proposes retirement (`feature-requests/FR-864-ramp-spike-to-governed.md:15-21`), then makes archive completion an acceptance criterion (`feature-requests/FR-864-ramp-spike-to-governed.md:179-180`). That is not mechanically inseparable from bootstrapping `deviant-daily` and must be judged on its own benefit/risk.

### R-4: Split the `deviant-daily` ramp application into a target-specific FR

Create a child FR for applying the ramp to `sheikkinen/deviant-daily`. It must cite the exact target commit(s), the existing target files to be changed, the test count and CI baseline, the requested tier, and the exact meaning of "Tier 2 + RTM". It must include hard repo-boundary conditions: do not vendor, submodule, archive, or commit the sibling repo into yamlgraph; no secret-bearing values or token-bearing logs may be copied; cross-repo work must preserve separate git indexes.

This split is required because FR-864 says `deviant-daily` is Tier 2 by the money-or-reputation clause, then includes the Tier 3 RTM explicitly (`feature-requests/FR-864-ramp-spike-to-governed.md:99-104`) and later requires "Tier 2 + RTM" plus CI and a deliberately failing commit witness (`feature-requests/FR-864-ramp-spike-to-governed.md:176-178`). That may be the right target policy, but it is a product/governance decision for the target repo and must be frozen in a target-specific FR rather than inferred from the generic ramp.

### R-5: Make each child FR's acceptance criteria exhaustive for its own surface

Rewrite acceptance criteria so each child FR can be tested without relying on another child being half-implemented. The current AC list checks Tier 1 dry-run and Tier 1 pre-commit installation (`feature-requests/FR-864-ramp-spike-to-governed.md:148-155`) but does not mechanically assert the full Tier 1 asset list from the tier table: CI job, Copilot guard set, and `AGENTS.md` (`feature-requests/FR-864-ramp-spike-to-governed.md:93-97`). It also requires graph lint/authoring evidence (`feature-requests/FR-864-ramp-spike-to-governed.md:159-161`) without pinning graph output schemas or draft paths beyond "tmp/" (`feature-requests/FR-864-ramp-spike-to-governed.md:120-121`, `181-182`).

For the installer child, criteria must cover tier 1, tier 2, and tier 3 dry-runs; no-overwrite/force behavior; installed hook/CI/template file presence; manifest content including yamlgraph commit SHA; and rollback/reversibility documentation. For graph children, criteria must cover graph lint, smoke, output schema validation, count reconciliation for corpus/test-file maps, zero auto-commit behavior, and at least one reviewed raw draft per graph before any generated governance artifact lands in a target repo.

### R-6: Keep detector and unenforced-repo warning out of all child scopes unless re-judged

Carry forward the current exclusion as a gate. The FR correctly states the spike detector and unenforced-repo warning are separate FRs (`feature-requests/FR-864-ramp-spike-to-governed.md:61-62`, `204-208`), and the diary itself locates the warning in `pre-command-guard.sh` (`docs/diary/diary-2026-08-23-nothing-announces-the-absent-guard.md:67-80`). Any child FR that touches those guard paths has become enforcement-infrastructure work and must be judged separately.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-864-ramp-spike-to-governed.md` marked Split, with links to child FRs and this judgement |
| D-2 | Child FR A: generic ramp installer and copyable asset manifest |
| D-3 | Child FR B: target-tailoring graph suite for doctrine/RTM/incidents |
| D-4 | Child FR C: `sheikkinen/deviant-daily` target application, including exact tier/RTM decision |
| D-5 | Child FR D: `scripture-dev` salvage and retirement |

Not authorized under FR-864 as written: implementing `scripts/ramp.sh`; creating or editing governed graph/prompt artifacts; modifying `deviant-daily`; modifying, archiving, or retiring `scripture-dev`; copying yamlgraph's hook/skill/doctrine assets into any target repo; changing `.github/hooks/`, CI, judge/review/graph-authoring doctrine, or detector/warning behavior; committing nested repos, submodules, target-repo archives, credentials, token-bearing logs, or generated target governance artifacts into yamlgraph.

## Revised acceptance criteria

- [ ] AC-01: FR-864 is updated to record this SPLIT verdict and links to the child FRs; its own Status becomes Split or equivalent non-enforcement state.
- [ ] AC-02: Child FR A freezes the generic installer surface, source asset inventory, tier asset matrix, dry-run/no-overwrite/force semantics, manifest format, and scratch-repo tests for every tier.
- [ ] AC-03: Child FR B freezes the governed graph artifacts, prompt artifacts, output schemas, draft output paths, graph-authoring evidence, graph lint/smoke commands, and human-review requirements for generated doctrine/RTM/incident drafts.
- [ ] AC-04: Child FR C freezes the target repo ref, target tier, RTM inclusion decision, exact target files, CI/test baseline, pre-commit installation proof, non-secret witness requirements, and hard sibling-repo boundary conditions for `deviant-daily`.
- [ ] AC-05: Child FR D freezes the `scripture-dev` source ref, full artifact population count, salvage disposition schema, lift criteria, FR-207 update requirement, and human approval gate for archive state changes.
- [ ] AC-06: Each child FR independently dispositions FR-207, FR-748, FR-826, FR-862, FR-863, and the three cited diary entries only where territorially relevant; irrelevant prior art must be explicitly marked as non-overlap rather than inherited wholesale.
- [ ] AC-07: No implementation work begins until the relevant child FR has its own judgement granting authority.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | FR-864 grants authority only to revise/split planning artifacts; it grants no code, graph, target-repo, or archival implementation authority. | GATE |
| C-2 | Do not invoke or re-run the judge while acting on this draft judgement; child FRs must later enter the normal judge route independently. | GATE |
| C-3 | Any `graph.yaml` or `prompts/*.yaml` creation/material modification in yamlgraph or a target repo must use the governed graph-authoring route and retain its report. | GATE |
| C-4 | Do not archive, delete, rename, transfer, or change settings on `scripture-dev` without an explicit human approval gate in its own child FR. | GATE |
| C-5 | Do not modify `pre-command-guard.sh`, CI enforcement, judge/review doctrine, or spike/unenforced-repo detector behavior under these child scopes unless a separate enforcement-infrastructure FR authorizes it. | GATE |
| C-6 | Cross-repo work must preserve repository boundaries: explicit target refs, explicit file lists, separate git statuses, no nested repo commits, and no secret/token/log artifacts copied across repos. | GATE |
| C-7 | Generated governance artifacts are drafts until human-reviewed; no graph may auto-commit into yamlgraph or a target repo. | GATE |

Authority granted: only to revise FR-864 into the split plan and create the child FRs above; no ramp implementation, graph authoring, target-repo changes, or `scripture-dev` archival is authorized by this judgement.
