# Feature Request: FR-894 Corpus Map-Reduce and GitHub Scope-Reconciliation Reference

**Priority:** MEDIUM
**Type:** Enhancement (documentation only)
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-08-26
**First consumer / first event:** the next agent asked to "read every commit or
PR and summarize it" or "find what changed beyond intended scope." At that
tool-selection moment, the agent finds one proven corpus pattern instead of
building an ad-hoc agent loop or treating a single global summary as exhaustive.

## Summary

Add `reference/patterns/corpus-map-reduce.md`, a reusable pattern for bounded
LLM analysis over a frozen corpus:

`freeze -> partition -> typed map -> deterministic reconciliation -> optional semantic reduce -> render`

Document two distinct uses of the same topology:

1. **Descriptive recap:** one short account per commit or pull request, reduced
   into a timeline or thematic summary.
2. **Authority-aware scope reconciliation:** compare each pull request's actual
   GitHub diff against an independent statement of intended scope, surfacing
   unexplained changes and missing intended deliverables for stronger review.

This FR documents an already-demonstrated architecture. It does not authorize a
new graph, GitHub integration, scorer, merge gate, or runtime feature.

## Value Statement

Agent operators get a cost-bounded, provenance-preserving way to analyze every
item in a repository corpus without silent omissions or falsely calling a
surprising change unauthorized when no independent authority exists.

## Problem

The reference documents the mechanics but not the complete analytical pattern:

- `reference/patterns.md` Pattern 8 explains map fan-out.
- `reference/patterns.md` Pattern 10 explains pre-chunking for rate limits.
- `reference/map-nodes.md` explains collection and reducer behavior.
- `reference/patterns/coded-classification.md` explains one specialized
  classification/reconciliation architecture.

None names the general corpus contract proven independently by:

- `examples/demos/prompt_theme_analyzer/graph.yaml`: normalize, map, aggregate,
  group, render with pinned `inception/mercury-2`.
- `examples/demos/fr-atlas/graph.yaml`: chunk a corpus, map semantic themes,
  reconcile coverage mechanically, synthesize.
- `examples/demos/req_witness_audit/graph.yaml`: batch a large question
  population and reject missing or hallucinated identities at reduce time.
- `examples/demos/session-shapes/graph.yaml`: cheap pinned-model map with a
  privacy-scrubbed deterministic reducer.
- `examples/demos/corpus_census/graph.yaml` (FR-892): the shipped reusable
  discover-extract-map-reduce skeleton with invocation-bound discovery and
  extraction adapters plus a fail-closed ledger reducer.
- `docs/the-questioner-and-the-trace.md`: a full-corpus run over 1,278 diary
  files using 83 map calls plus 11 reductions, with exact byte and item
  reconciliation and no skipped map failures.

The absence matters because "summarize these changes" and "what changed that
was not supposed to change?" look similar but have different epistemic
contracts.

A recap needs observed facts. A scope finding needs two independent planes:

- **Authority plane:** what change was permitted or required.
- **Reality plane:** what the immutable GitHub diff actually changed.

A commit message or PR body is authored by the same change producer and is
therefore description, not independent authority. Without a governing issue,
FR, judgement, acceptance criteria, or equivalent frozen scope artifact, the
strongest honest label is `unexplained` or `surprising`, never `unauthorized`.

The existing `examples/demos/recap/graph.yaml` gives one synthesis judgement
over a capped commit window. It does not produce one accounted result per
commit, reconcile every input identity, or compare changes against frozen
authority. The existing PR review route correctly compares one PR against its
FR and judgement; it is a merge-review instrument, not a cheap historical
corpus census.

## Ideal Result

When an agent encounters an enumerable GitHub or file corpus, it can recognize
the task shape, choose a cheap pinned model for bounded per-item judgements,
prove mechanically that every frozen input was accounted for, and distinguish
description from authority. A corpus run can triage or explain history without
claiming merge-review authority, while any flagged live PR still enters the
independent `scripts/review.sh` route.

## Proposed Solution

### 1. Add the reference pattern

Create `reference/patterns/corpus-map-reduce.md` and link it from:

- `reference/README.md` under Examples & Guides.
- Pattern 8 and Pattern 10 in `reference/patterns.md`, without duplicating map
  syntax already owned there.

The document owns architecture and evidence contracts, not YAML syntax.

### 2. Define the six-stage topology

The reference must describe these stages:

1. **Freeze:** corpus-specific discovery and extraction adapters enumerate the
  population and a deterministic collector records immutable source identity,
  content hash, and corpus bounds before any model call. GitHub records use
  commit SHA or PR number plus base/head SHA; a moving branch name is not an
  identity. FR-892 tool slots are the executable adapter precedent.
2. **Partition:** split by a declared character/token budget, not merely file
   count. Oversized records retain source span metadata.
3. **Map:** make one bounded, typed judgement per item or partition. Pin a
  cheap model when the judgement is narrow. A map error must fail the overall
  run, either directly or when deterministic reconciliation rejects the
  resulting missing/error identity. `on_error: skip` is allowed only with
  that fail-closed reducer contract (the FR-892 pattern).
4. **Reconcile:** deterministic code rejects unknown IDs, duplicates, missing
   inputs, malformed source references, and arithmetic supplied by the model.
   It computes coverage and actual call counts.
5. **Reduce:** optionally map/reduce the short memoranda hierarchically. No
   reduction is allowed to erase the primary per-item findings.
6. **Render:** write a full provenance-bearing artifact plus a compact human
   index. An exit code without the artifact is failure.

### 3. State the mechanical invariants

The pattern must require:

- Every frozen input item or byte span belongs to exactly one primary map
  payload.
- Every primary payload produces exactly one typed result.
- Every result belongs to exactly one reduction batch when reduction is used.
- Model-emitted source IDs are reconciled against collector-owned IDs.
- Counts, coverage, hashes, and cost/call totals are computed in code.
- Provider, model, corpus identity, and run identity are recorded.
- No silent map dropout is accepted.

### 4. Document GitHub descriptive recap

Provide a worked application, not a new executable graph:

- **Commit input:** commit SHA, author/date, subject/body, diff/stat, and linked
  PR identity when available.
- **PR input:** PR number, base/head SHA, title/body, linked issue or FR,
  changed-file/diff payload, checks, and merge state.
- **Map result:** concise recap, files/surfaces affected, evidence references,
  and uncertainty.
- **Reduce result:** chronology, themes, concentrated churn, and unresolved
  anomalies while preserving links to every primary recap.

The reference must recommend pull requests as the semantic unit when they
exist. Fixup commits are transport fragments; a squash commit should inherit
the associated PR recap rather than be interpreted as an independent intent.

### 5. Document authority-aware scope reconciliation

Define an explicit authority hierarchy:

1. Governing FR plus independent judgement or equivalent frozen specification.
2. Issue/specification with testable acceptance criteria.
3. PR body with explicit in-scope and out-of-scope statements.
4. Commit message.

Levels 3 and 4 are self-description, not independent authority. They may
support `unexplained` findings but cannot independently justify
`unauthorized`.

Each mapped PR reconciliation should preserve fields equivalent to:

```yaml
pr: 123
base_sha: "..."
head_sha: "..."
authority_sources: ["feature-requests/FR-XXX-....md", "...judgement.md"]
authorized_changes: []
unexplained_changes: []
missing_deliverables: []
out_of_scope_matches: []
evidence: []
confidence: low | medium | high
```

The reference must distinguish:

- **Path-level drift:** files or directories outside an explicit scope fence.
- **Semantic drift:** an allowed file changed in a way the authority does not
  permit.
- **Omission:** an authorized deliverable has no corresponding change or
  evidence.
- **Metadata drift:** PR body, head SHA, checks, or local state disagree with
  GitHub reality.

### 6. Preserve the review boundary

Mercury-2 or another cheap model may summarize and triage a historical corpus.
Its findings are claims, not merge verdicts. A live PR flagged by the corpus
run must still be reviewed through `scripts/review.sh`, whose input closure,
validation requirement, model pin, and human merge decision remain unchanged.

### 7. Document cost and privacy bounds

Include a simple estimate:

`calls = primary partitions + reduction batches`

The collector must refuse a corpus above declared item/token/call ceilings
before spending. The reference should name `inception/mercury-2` and
`anthropic/claude-haiku-4-5` as demonstrated cheap structured-output choices,
not universal defaults.

Public GitHub history can use an external provider. Private repository diffs,
secrets, customer code, and regulated material require an approved provider or
local model; collection must exclude credentials and oversized binary patches
before the model boundary.

## Acceptance Criteria

- [ ] `reference/patterns/corpus-map-reduce.md` exists and is linked from
      `reference/README.md`.
- [ ] Pattern 8 and Pattern 10 in `reference/patterns.md` link to the new
      reference without duplicating its content.
- [ ] The reference documents freeze, partition, typed map, deterministic
      reconciliation, optional hierarchical reduce, and render stages.
- [ ] The seven coverage/provenance invariants above are stated as requirements,
      not optional advice.
- [ ] A commit/PR recap worked application names immutable GitHub identities and
      preserves one primary result per semantic unit.
- [ ] A scope-reconciliation worked application separates authority from
      reality and covers path drift, semantic drift, omission, and metadata
      drift.
- [ ] The wording rule is explicit: absent independent authority, findings are
      `surprising` or `unexplained`, never `unauthorized`.
- [ ] The reference states that PRs are the preferred semantic unit and commits
      are a fallback/transport unit.
- [ ] The reference states that cheap-model corpus triage cannot issue a merge
      verdict and points live findings to `scripts/review.sh`.
- [ ] Cost ceilings, call-count arithmetic, provider pinning, privacy, secret,
      and binary-patch boundaries are documented.
- [ ] The pattern cites at least the FR-402 prompt-theme analyzer, FR-748 atlas,
      FR-851 requirement-witness audit, FR-884 session-shapes classifier,
      FR-892 corpus census, `recap`, and review-pr precedents.
- [ ] No `graph.yaml`, prompt, Python tool, runtime, CLI, hook, CI, capability,
      requirement, or GitHub API integration is added or changed under this FR.
- [ ] Exact validation records these commands and results:
  `rg -n '[[:blank:]]+$' reference/patterns/corpus-map-reduce.md reference/README.md reference/patterns.md` (no matches);
  a script that resolves every workspace-relative Markdown link in the
  three touched reference files and exits nonzero for a missing target;
  and `git diff --check -- reference/patterns/corpus-map-reduce.md reference/README.md reference/patterns.md`.

## Alternatives Considered

### Extend only `reference/map-nodes.md`

Rejected. That document owns map syntax and execution behavior. Corpus
freezing, provenance, hierarchical reduction, and authority comparison are an
architectural pattern above the node contract.

### Unpark FR-857 or build another generic corpus graph

Rejected. FR-892 now ships the reusable discover-extract-map-reduce skeleton
with injected adapters. FR-857 remains a parked earlier proposal whose
question-first semantic-grep surface is not needed to document the proven
architecture. This FR adds no second executable surface.

### Extend `examples/demos/recap/graph.yaml`

Rejected. Recap intentionally performs one synthesis over a bounded time
window. Per-item exhaustive reconciliation and authority-aware review are
different contracts and would overload a quiet existing graph.

### Run the full PR reviewer over every historical PR

Rejected. The reviewer is a strong, validation-bearing merge instrument with
human authority at the end. Historical corpus triage should be cheaper and
parallel, then escalate only flagged live PRs to that route.

### Build a GitHub collector and scope-audit graph in this FR

Rejected. A reference pattern is the minimal response to the repeated
architecture. Executable GitHub collection needs a named repository/window,
API pagination and rate-limit contracts, private-data policy, fixtures, and a
separately judged first consumer.

## Related

**Prior art disposition:**

- `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md` is the
  shipped reusable executable skeleton. Kept as the primary implementation
  precedent; this FR supplies the higher-level corpus, authority, provenance,
  and GitHub application contract missing from its slot/runtime reference.
- `feature-requests/FR-857-corpus-analysis-fanout-graph.md` is a parked earlier
  proposal. Kept without changing its status; FR-892 now owns the generic
  executable skeleton, while FR-857's semantic-grep framing remains separate.
- `feature-requests/FR-855-generated-pattern-index.md` is a deterministic
  discoverability index. Kept; it may make this reference discoverable but
  does not define the corpus execution contract.
- `examples/demos/recap/graph.yaml` is the existing one-judgement change recap.
  Kept; its bounded summary contract remains narrower.
- `.github/skills/review-pr/doctrine.md` and `scripts/review.sh` own live PR
  merge review. Kept and explicitly protected from cheap-model substitution.
- `examples/demos/prompt_theme_analyzer/graph.yaml`,
  `examples/demos/fr-atlas/graph.yaml`,
  `examples/demos/req_witness_audit/graph.yaml`, and
  `examples/demos/session-shapes/graph.yaml` are demonstrated architecture
  witnesses. Kept; no extraction or modification under this FR.
- `reference/patterns/coded-classification.md` remains the specialized
  controlled-vocabulary pattern. Kept; corpus map-reduce is broader and does
  not require a code taxonomy.
- `reference/patterns/batch-runner.md` remains the pattern for invoking one
  graph independently over runtime-selected files. Kept; this FR maps bounded
  semantic judgements inside one corpus run and reconciles them collectively.

## Triage (generated — claims requiring disposition)

- [pending] canon: would_you_use_this: agent operators building corpus analysis tasks (first consumer named in Summary and Value Statement)
- [pending] canon: who_reads_this_when: agent operators at tool-selection moment when asked to summarize corpus or find scope drift (delivery rung named in Summary)
- [pending] canon: does_the_platform_already_do_this: FR-892 ships reusable discover-extract-map-reduce skeleton; FR-402, FR-748, FR-851, FR-884 demonstrate the pattern; this FR documents the architecture and authority contract missing from reference (prior art dispositioned)
- [pending] pre-mortem: Reference document ships but links in reference/patterns.md and reference/README.md are broken or point to nonexistent anchors, breaking discoverability at tool-selection moment
- [pending] pre-mortem: Acceptance criterion on trailing whitespace or link validation fails: rg or link-resolver script finds missing targets or whitespace in touched files, blocking merge
- [pending] pre-mortem: Authority hierarchy section omits explicit guidance that commit messages are self-description not independent authority, allowing agents to call changes 'unauthorized' without frozen scope artifact
- [pending] pre-mortem: Worked application for scope reconciliation names fields but does not show how to mechanically distinguish path drift from semantic drift, leaving agent operators to invent reconciliation logic anyway
- [pending] pre-mortem: Reference document cites FR-892 but does not explain how to use its discover-extract-map-reduce skeleton with injected adapters, forcing operators to reverse-engineer from corpus_census graph.yaml instead of following pattern
- [pending] value-prop: For agent operators (whom), kills silent omissions and falsely-authorized changes in corpus analysis (pain), vs ad-hoc agent loops or treating single global summary as exhaustive (alternative) — completable from FR text as stated
