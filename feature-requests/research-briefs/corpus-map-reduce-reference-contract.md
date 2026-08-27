# Problem brief: corpus analysis has execution machinery but no canonical evidence contract

**Prior art:** dispositioned in the FR this brief informs (closed-input brief
per FR-890).

## Problem statement

The repository now contains a reusable `corpus_census` graph (FR-892) and
several specialized corpus graphs. They can discover and extract items, run a
cheap per-item LLM judgement, and reconcile results in deterministic code.
Reference documentation explains map-node mechanics, pre-chunking, tool slots,
and one specialized coded-classification pattern, but no single reference
states the general evidence contract for exhaustive semantic corpus analysis.

This gap became concrete in two tasks on 2026-08-26:

1. A full diary reading needed to prove that every one of 1,278 committed files
   and every non-empty byte entered exactly one primary map payload, that every
   payload produced one finding, and that reductions did not replace primary
   evidence.
2. A proposed GitHub-history use needed to distinguish a descriptive recap
   (what each commit or PR changed) from authority-aware reconciliation (what
   changed beyond independently frozen scope). A PR body or commit message is
   written by the same change producer and cannot independently authorize its
   own diff.

Without a reusable contract, agents can run the right topology while still
silently dropping map failures, trusting model-emitted identities, computing
counts in prose, erasing per-item findings during synthesis, or calling a
surprising change unauthorized when no independent authority exists. The
problem is not missing fan-out capability. It is that execution, evidence,
authority, cost, privacy, and escalation rules remain scattered across demos,
FRs, and diary incidents.

## Classification

judgement/analysis/generation

## Constraints

- FR-892 is completed and owns the reusable executable
  discover-extract-map-reduce skeleton with invocation-bound discovery and
  extraction adapters. Do not duplicate or replace it.
- `reference/map-nodes.md` and Pattern 8 own map syntax; Pattern 10 owns
  pre-chunking mechanics; `reference/graph-yaml.md` owns tool-slot syntax.
- The live pull-request merge verdict remains exclusively in
  `scripts/review.sh` under the independent review doctrine and human merge
  decision.
- The work must not add or modify graphs, prompts, Python tools, runtime, CLI,
  hooks, CI, capabilities, requirements, GitHub API integration, scorers, or
  merge gates.
- Any useful result must be discoverable by an agent at the moment it is asked
  to read an enumerable corpus, not only archived in an FR or diary.
- Provider/model choice must respect repository visibility, private/customer
  data, secrets, binary patches, and regulated material.
- Model outputs are claims. Immutable source identity, coverage, arithmetic,
  and failure semantics belong in deterministic code.

## Witnessed incidents

- The diary discourse run used 83 primary Mercury-2 map calls and 11 reduction
  calls over 4.6 MB of text. Its value depended on deterministic byte and item
  reconciliation; a zero exit code without the dossier occurred once when the
  executable was absent from PATH, proving artifact existence is the contract.
- FR-884 found 74 session records could be classified cheaply but raw reading
  was still needed to interpret aggregate token shares; reduction cannot
  replace primary evidence.
- FR-851 rejects hallucinated or missing requirement IDs at reduce time.
- FR-892 intentionally uses `on_error: skip` in its map but its LLM-free reducer
  rejects map errors and missing indices, proving skip can remain fail-closed
  only when reconciliation owns completeness.
- `examples/demos/recap/graph.yaml` gives one useful bounded synthesis but does
  not preserve one accounted result per commit or compare changes against
  independent authority.
- The independent PR review doctrine already separates GitHub diff reality
  from governing FR/judgement authority for one live PR; historical corpus
  triage must not weaken or impersonate that route.
