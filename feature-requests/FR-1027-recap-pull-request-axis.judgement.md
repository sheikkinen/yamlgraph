# Judgement: FR-1027 Recap Pull-Request Axis

**Route:** `scripts/judge.sh` (Copilot backend), 2026-09-07, JUDGE_WORKDIR=worktree. Promoted verbatim from `tmp/draft-judgement-copilot-FR-1027-recap-pull-request-axis.md`. R-1..R-5 folded into the FR (C-1); no re-judge — round 1 of the FR-1022 two-round budget.

**Note on omission:** this judgement carries no `### Questions for the human` section. Per FR-740 absence is an omission, not a statement of "none". The two decisions that are the human's are recorded in the FR fold instead: C-3 (workflow credential wiring approval before merge) and C-7 (whether `RECAP_PAT` can read PR metadata, unverifiable from outside the secret).


**Verdict:** APPROVED WITH REVISIONS — the code-owned pull-request axis is a sound extension of the existing recap example, but authority activates only after the FR precisely bounds the hosted-data call, preserves the exact git window, and makes partial and unavailable output unambiguous.

**Reviewed against:** `feature-requests/FR-1027-recap-pull-request-axis.md`; cited research `feature-requests/FR-1027.research.md`; cited precedent `feature-requests/FR-700-timeframe-recap-example.md`, `feature-requests/FR-702-recap-disposition-axis.md`, `feature-requests/FR-703-recap-status-join-post-pass.md`, `feature-requests/FR-704-recap-orphans-bypass-model.md`, `feature-requests/FR-821-weekly-recap-automation-pr.md`, `feature-requests/FR-922-recap-bare-repo-test-skip-and-latency-investigation.md`, `feature-requests/FR-922-recap-bare-repo-test-skip-and-latency-investigation.judgement.md`, `feature-requests/FR-930-recap-code-owned-fr-reference-reconciliation.md`, `feature-requests/FR-930-recap-code-owned-fr-reference-reconciliation.judgement.md`; cited implementation evidence `examples/demos/recap/graph.yaml`, `examples/demos/recap/nodes/partition.py`, `examples/demos/corpus_census/adapters/corpus_adapters.py`, `scripts/weekly_recap.py`, `.github/workflows/weekly-recap.yml`, `tests/unit/test_recap_demo.py`, `tests/integration/test_recap_demo_integration.py`, `capabilities/CAP-195-timeframe-recap-demo.yaml`, `CLAUDE.md`; repo doctrine `.github/copilot-instructions.md`, `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The problem and first consumer are concrete. The current recap graph has one LLM node and routes deterministic collection through a final code-owned post-pass (`examples/demos/recap/graph.yaml:96-115`, `examples/demos/recap/graph.yaml:129-134`), while the renderer exposes only workstreams, orphans, and hotspots (`scripts/weekly_recap.py:35`, `scripts/weekly_recap.py:102-123`). Open and closed-unmerged pull requests therefore cannot be recovered from the present local-git artifact.

The proposed boundary is architecturally appropriate. `finalize_recap` already owns code-only assembly and preserves model-independent fields (`examples/demos/recap/nodes/partition.py:178-203`); FR-1027 keeps PR numbers, dates, duration, and titles out of the prompt and preserves the two-field prompt schema (`FR-1027:218-228`). The existing structure tests already freeze exactly one LLM node, the tool-node set, portable git commands, and prompt fields (`tests/unit/test_recap_demo.py:24`, `tests/unit/test_recap_demo.py:48-101`), so direct RED witnesses can be derived without inventing a new abstraction.

The research record is substantive. It contains four distinct solution classes, preserves the Subtractionist's outright dissent, records the timeline-API disagreement, and answers `is_this_a_graph` by identifying the existing recap graph (`FR-1027.research.md:15-27`, `FR-1027.research.md:33-50`, `FR-1027.research.md:75-80`). That satisfies the local research gate's demand for genuine alternatives, disagreement, precedent, and the graph-fit answer (`.github/skills/judge-fr/doctrine.md:118-128`). Prior recap, post-pass, reconciliation, automation, latency, and census work is distinguished rather than merely listed.

The scope is one concern: add a deterministic hosted pull-request decision axis to an existing example and its existing renderer/cron consumer. Strategic classification: **contrib/example**. It serves the operator's Monday recap and cross-repository diagnostic use, while existing graph and post-pass abstractions fit with a bounded graph-local gap; no framework primitive is warranted (`.github/skills/judge-fr/doctrine.md:51-56`).

## Required revisions

### R-1: Preserve the exact git window and define deterministic ordering

Amend Proposed Solution and AC-05 through AC-07 so `git rev-parse --since=<since>` supplies an exact epoch used directly for membership comparisons. Converting that epoch to `YYYY-MM-DD` is permitted only for displayed dates; it must not truncate the comparison boundary to UTC midnight. Define inclusive membership as `mergedAt >= epoch` and, only when `mergedAt` is null, `closedAt >= epoch`.

Define code-owned stable ordering: merged and closed-unmerged rows sort by their decision timestamp descending and then PR number descending; open rows sort by `createdAt` descending and then PR number descending. Tests must scramble fixture input and assert exact ordered output. This makes "deterministically" testable rather than dependent on undocumented `gh` response order.

### R-2: Bound and normalize the hosted-data boundary

Replace the research/solution phrase "one network call" with "exactly one `gh` subprocess invocation." `gh pr list --limit 300` may paginate internally, so the FR cannot promise one HTTP request. Add a finite timeout matching the cited precedent's `GH_TIMEOUT = 60` (`examples/demos/corpus_census/adapters/corpus_adapters.py:98-106`).

Specify narrow handling for `FileNotFoundError`, `subprocess.TimeoutExpired`, `subprocess.CalledProcessError`, and invalid JSON/required-field shape. Each must return `available: False`, empty buckets, and a stable non-empty reason; a non-zero exit with blank stderr must fall back to an exit-code reason. Do not add a broad catch. Invalid `since` and non-repository failures remain loud because the existing git collection contract already fails those inputs.

### R-3: Reconcile the remote-form contract

Amend the Identify step to include every form required by AC-04: `https://github.com/o/n[.git]`, `git@github.com:o/n[.git]`, and `ssh://git@github.com/o/n[.git]`. Define malformed GitHub URLs, missing owner/name segments, local/file remotes, and non-GitHub hosts as unavailable with stable specific reasons and no `gh` invocation. Add a test proving a crafted remote string remains one fixed subprocess argument and cannot alter argv.

### R-4: Make cap and renderer semantics honest

Replace "truncated" as a proven fact with "cap reached; results may be truncated": exactly 300 returned rows cannot prove that a 301st row exists. State explicitly that `merged`, `closed_unmerged`, and `open` contain all matching rows **within the capped response**, not necessarily every open PR in a repository when the cap is reached.

Define one axis-level note placement that cannot disappear when buckets are non-empty. `render_markdown` must emit the note once before the three PR sections whenever the axis is unavailable or the cap is reached. When unavailable, each section renders `(not collected)` rather than `(none)`; when available, empty buckets render `(none)`. Add exact-output tests for available-empty, unavailable, cap-reached-with-items, and cap-reached-with-empty-bucket cases. The current wording only says a note renders "in place of `(none)`" (`FR-1027:232-235`, `FR-1027:288-291`), which can suppress a cap warning when a bucket contains rows.

### R-5: Name and mechanically verify the real-run witness

Replace AC-13's unnamed committed output with `feature-requests/FR-1027.witness.md`. Require that file to record the run date, repository slug, exact `since` input, collection timestamp, cap status, and the three code-owned PR buckets. A test or verification command must assert that the closed-unmerged section contains a line beginning `#627|`; prose saying the witness "shows #627" is not sufficient. If implementation occurs after #627 has aged out of the requested window, use fixed explicit window bounds that include its recorded close timestamp and record those bounds in the witness.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-1027-recap-pull-request-axis.md` folds R-1 through R-5 and records implementation decisions/status. |
| D-2 | `examples/demos/recap/graph.yaml` registers and sequences one graph-local PR collection python node; `examples/demos/recap/prompts/recap.yaml` remains byte-identical. |
| D-3 | `examples/demos/recap/nodes/prs.py` owns remote parsing, exact-window filtering, one bounded `gh` invocation, validation, stable sorting, line assembly, and typed available/cap state. |
| D-4 | `examples/demos/recap/nodes/partition.py` attaches only the code-owned PR buckets and axis note in the existing final post-pass. |
| D-5 | `scripts/weekly_recap.py` renders the axis; `.github/workflows/weekly-recap.yml` supplies the existing `RECAP_PAT` as `GH_TOKEN` to the recap step. |
| D-6 | `tests/unit/test_recap_demo.py`, `tests/integration/test_recap_demo_integration.py`, and committed PR JSON fixtures directly witness parsing, argv, timeout/error normalization, exact filtering/order/format, cap semantics, post-pass preservation, renderer output, workflow token wiring, and no-network bare-repo behavior. |
| D-7 | `capabilities/CAP-195-timeframe-recap-demo.yaml`, regenerated `ARCHITECTURE.md`, `examples/demos/recap/README.md`, one changelog fragment, `feature-requests/FR-1027.witness.md`, and the required diary distillation record the capability and evidence. |

Not authorized: a second recap graph; any `yamlgraph/` framework change; prompt or LLM schema changes; an additional LLM call or per-PR classification; review-round/timeline collection; commit-to-PR joining; extending FR/NC or `#N` reconciliation; a required graph input for a GitHub token; more than one `gh` subprocess invocation per recap; removal, skip, or network coupling of the bare-repo integration witness; new workflow permissions or a new credential.

## Revised acceptance criteria

- [ ] AC-01: `yamlgraph graph lint examples/demos/recap/graph.yaml` passes and the graph has exactly one LLM node, `synthesize`.
- [ ] AC-02: `prompts/recap.yaml` is byte-identical to its pre-change content; its schema fields are exactly `{workstreams, hotspots}` and its template references no PR state.
- [ ] AC-03: The existing tool-node set and every existing `type: shell` command remain unchanged; `test_collection_is_tool_nodes` and `test_git_commands_are_portable` pass unmodified.
- [ ] AC-04: Unit tests accept the three GitHub remote families and optional `.git` suffix from R-3; missing, malformed, local/file, and non-GitHub remotes return stable unavailable reasons and never invoke `gh`.
- [ ] AC-05: A unit test proves `--since=<since>` is passed as one argv element to `git rev-parse`, the exact returned epoch controls inclusive timestamp membership, and UTC date conversion is display-only.
- [ ] AC-06: A scrambled committed fixture proves exact bucket membership and R-1 ordering for in-window merged, before-window merged, in-window closed-unmerged, before-window closed-unmerged, and old open PRs.
- [ ] AC-07: Every line equals `#<number>|<created>→<end>|<N>d|<title>` exactly, including fixture title bytes; duration is whole elapsed UTC days.
- [ ] AC-08: Exactly one fixed-argv, `shell=False` `gh` subprocess invocation is attempted for an eligible remote, with a 60-second timeout; a crafted remote cannot add or split argv.
- [ ] AC-09: Missing `gh`, timeout, non-zero exit with and without stderr, invalid JSON, and missing required JSON fields each yield `available: False`, empty buckets, and a stable non-empty reason through narrow exception handling.
- [ ] AC-10: Available zero-row output is distinct from unavailable output; no error branch fabricates populated buckets.
- [ ] AC-11: A 300-row fixture marks `cap_reached: True` and reports that results may be truncated; a 299-row fixture does not. The contract claims completeness only within the returned capped response.
- [ ] AC-12: `finalize_recap` attaches the three buckets and one axis note while leaving `workstreams`, `orphans`, `hotspots`, and `unverified_refs` behavior unchanged; inherited FR-702/703/704/930 tests pass unmodified.
- [ ] AC-13: Exact renderer tests cover available-empty as `(none)`, unavailable as one visible axis note plus `(not collected)`, and cap-reached output with both non-empty and empty buckets; existing section headings and order are preserved.
- [ ] AC-14: The bare-repo integration fixture has no origin and makes no `gh` call; the complete recap records the absent-origin note without adding a second slow/network path.
- [ ] AC-15: `feature-requests/FR-1027.witness.md` contains the metadata required by R-5 and a closed-unmerged line beginning `#627|`, verified mechanically.
- [ ] AC-16: `.github/workflows/weekly-recap.yml` passes `${{ secrets.RECAP_PAT }}` as `GH_TOKEN` only to the recap step, verified by a workflow-YAML test.
- [ ] AC-17: RED tests and GREEN implementation are separate commits and `git log` shows that order.
- [ ] AC-18: `CAP-195` contains `REQ-YG-669`; every new test carries `@pytest.mark.req("REQ-YG-669")`; regenerated `ARCHITECTURE.md`, strict requirement coverage, targeted recap tests, graph lint, README, changelog fragment, FR implementation notes, and diary distillation are present and passing.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-5 into FR-1027 before implementation authority activates. | GATE |
| C-2 | Because `graph.yaml` is materially modified, implementation must use the repository's governed graph-authoring route and preserve its validation report. | GATE |
| C-3 | Human review must approve the `.github/workflows/weekly-recap.yml` credential wiring before merge; workflow changes are enforcement-infrastructure input (`.github/skills/judge-fr/doctrine.md:98-99`). | GATE |
| C-4 | The PR axis must remain code-owned and must never enter the synthesis prompt, model schema, model-visible variables, or reconciliation universe. | GATE |
| C-5 | No broad exception handler, silent fallback, unlimited subprocess wait, fabricated empty-success state, or raw error path that can erase the unavailable distinction is permitted. | GATE |
| C-6 | Reaching 300 rows must visibly qualify the whole axis as potentially partial; no section may claim repository-wide completeness after the cap is reached. | GATE |
| C-7 | If the existing `RECAP_PAT` cannot read PR metadata, stop and return to planning rather than adding workflow permissions, another secret, or an input token under this authority. | GATE |

Authority granted: after the required revisions are folded in, the enforcer may add the single bounded, deterministic PR collection node and wire its code-owned buckets through the existing recap finalizer, renderer, scheduled workflow, tests, registry, documentation, and named witness surfaces listed above.
