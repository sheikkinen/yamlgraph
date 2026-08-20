# Judgement: FR-836 GitClaw Candidate Output Contract

**Verdict:** ENFORCED - R-1 through R-3 were folded before implementation;
canonical commit `2a0a3c4fbb53d81884ca162dcf3c714b96a99e9b` and consumer
commit `33ec4467f7ed06d3b156695af7959b2e9fa35c77` were separately
human-approved and published on 2026-08-20. All 20 acceptance criteria pass,
including three recognized actual-source witnesses, so FR-831 Task 6 is
unblocked.

**Prior art:** FR-827 and FR-828 establish the forkable runner and failed
monolithic Oulu predecessor; preserve their runner/product evidence without
retrying issue #1. FR-829 and FR-830 preserve public-read policy and ledger
identity. FR-831 stages Task 6; FR-832 through FR-834 provide immutable source
witnesses; FR-835 provides the composition envelope. FR-836 repairs only the
shared candidate-output boundary and does not supersede those contracts.

**Reviewed against:** `feature-requests/FR-836-gitclaw-candidate-output-contract.md`;
FR-831 through FR-835 and their judgements; repository judge doctrine,
judgement template, and Copilot instructions. The cited canonical GitClaw
commit `ff200831962eb34158e77a4c38919776e21800bf` is external to this repository
and was not consumed by the sole-route judge; the FR contains its bounded
behavioral disposition.

## What is sound

The problem is specific and reproduced: three source runs failed with
`no output in state` while `candidate` was present among returned keys, and the
direct baseline probe returns `None` for a non-empty plain candidate whose
feature slug differs. This is a shared runtime-boundary defect, not a source or
Task 6 implementation defect.

The selected contract is narrow and fail-closed. Legacy feature-slug extraction
runs first, exact `candidate` extraction runs second, and the committed
self-nested custom-key fallback remains. Arbitrary plain state strings are not
scanned, so `date`, `run_instant`, `source_snapshots`, metadata, or error text
cannot become publishable output after node failure.

The strategic classification is **framework primitive for GitClaw**. It defines
the generated-feature output boundary used by the three independently governed
source features and the pending composer. FR-831 Task 6 remains blocked until
the repair, exact consumer rollout, and actual source witnesses complete.

## Required Revisions

### R-1: Disposition every declared dependency

**Folded.** The Prior Art Disposition table now names FR-829 and FR-830.
FR-829's bounded public-read and same-directory invariants remain unchanged;
only its generated-feature policy file may name the output key. FR-830's
repository-scoped append-only ledger remains entirely outside the change.

### R-2: Name the exact enforcement surfaces

**Folded.** The FR freezes nine canonical and consumer paths:
`tools/cron_run.py`, three focused test files,
`policy/generated-features.md`, and the four plan/judge/enforce/review prompts.
Every other path, including README, source features, workflows, dependencies,
ledger/state, containment, and outputs, remains unchanged.

### R-3: Make commands and retained artifacts explicit

**Folded.** The FR records exact canonical focused/full commands, consumer
synthetic/full commands, parity-hash command, and a bounded actual-source
witness command. It names five local evidence artifacts and prohibits retained
candidate text, raw responses, secrets, or environment values.

## Scope Is Frozen

| Deliverable | Surface |
|---|---|
| D-1 | Canonical red/green extraction tests for exact plain/nested `candidate` and metadata exclusion |
| D-2 | `tools/cron_run.py` output extraction only: feature slug, exact `candidate`, retained self-nested fallback, then fail closed |
| D-3 | Generated-feature policy requiring one non-empty final output at `state_key: candidate` |
| D-4 | Plan, judge, enforce, and review prompts requiring and verifying the same exact key |
| D-5 | Synthetic composition regression proving unchanged candidate envelope bytes and composer execution |
| D-6 | Human-reviewed canonical diff and exact hash-verified Oulu consumer rollout |
| D-7 | Consumer synthetic and bounded actual-source witnesses without retained source content |
| D-8 | FR closure evidence before Task 6 filing |

Not authorized: Task 6 filing or implementation; source graph/adapter edits;
source rediscovery; LLM synthesis; bulletin output; issue #1 action; cron
cadence, workflow, dependency, secret, ledger, containment, notification, or
publication changes; graph parsing inside cron; arbitrary state-string
scanning; or stale output reads.

## Conditions for Enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Human review approves this judgement and folded FR before implementation starts. | GATE |
| C-2 | A direct red test proves the plain custom-key defect before runtime code changes. | GATE |
| C-3 | Extraction checks only feature slug, exact `candidate`, and the retained self-nested fallback. | GATE |
| C-4 | Invalid, empty, missing, metadata-only, or structurally invalid output fails closed. | GATE |
| C-5 | Human review approves the exact canonical infrastructure diff before canonical commit/push. | GATE |
| C-6 | Consumer rollout copies only exact reviewed files with matching hashes and separate human approval. | GATE |
| C-7 | Live witnesses retain only recognition, candidate byte count, and declared health. | GATE |
| C-8 | Task 6 is not filed until all three committed Oulu source outputs are recognized. | GATE |

Authority granted: only after C-1, implement the tests-first canonical
`candidate` output-contract repair and exact consumer rollout. Canonical push,
consumer push, and Task 6 remain separately gated by C-5 through C-8.
