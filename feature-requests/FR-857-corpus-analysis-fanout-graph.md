# Feature Request: Generic Corpus-Analysis Fan-Out Graph

**Priority:** LOW — PARKED 2026-08-22: demand-driven; do not judge until a
firing moment recurs after FR-855 lands (see Devil's Advocate note)
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-22
**First consumer / first event:** the next corpus audit (tests, docs,
capabilities, diary, FR sequences) — historically launched as hand-run
subagent batches; first event: the next "read every file in this list
and report" task.

## Summary

A reusable map-node graph: file-list partitions in, per-partition LLM
analysis fanned out in parallel, merged findings artifact out — the
graph-native form of the 8-subagent hand-run corpus audit. Two modes of
the same machinery, selected by question + schema:

1. **Exhaustive audit** — "analyze every file against Q"; the contract
   is coverage (reconciliation proves nothing was skipped).
2. **Semantic grep** — "I want to know X; find related information";
   per-batch schema is `relevant: bool + excerpts + why`, most batches
   return nothing, the deliverable is the needles. Brute-force parallel
   read with a cheap model: no embedding index, no staleness, no
   retrieval misses — the complement to the RAG examples, affordable at
   repo scale (FR-851 precedent: 412 questions / 41 haiku batches).

## Value Statement

Corpus audits become one command with parallel execution, typed output,
and a durable findings artifact — instead of N sequential hand-composed
subagent briefs whose findings live only in chat.

## Problem

Census evidence: cluster C1 (`docs/2026-07-29-research-subagent-promotion.md`)
— eight near-identical "THOROUGH analysis. Read every test file listed
below…" subagent briefs in a single session/day (2026-05-30), a
`type: map` fan-out executed by hand. The 08-22 delta census shows the
shape recurring as corpus-style research briefs (FR-784+ sequence audit,
ninchat_voice usage audit). Discriminators hit: contract-shaped output,
reuse across corpus types, two-strike exceeded ×8 in one day. Subagents
are sequential-blocking; the map node is the native parallel primitive
(`first_person_tool_horizon`, diary 2026-08-22).

## Ideal Result

`yamlgraph graph run examples/demos/corpus_analysis/graph.yaml --var
manifest=partitions.yaml --var question="..."` fans the partitions
across a map node, each batch analyzed against the caller's question
with a typed findings schema, reconciled at the boundary (FR-851
discipline: no silent drops, hallucinated ids rejected), and merged into
one findings report.

## Proposed Solution

Authored via the governed route (`scripts/author.sh`), precedent
`examples/demos/map/graph.yaml` and the FR-851 census graph
(`examples/demos/req_witness_audit/`):

- **partition tool** (python): read a manifest of file lists (or glob +
  batch size), emit batches.
- **analyze** (map over batches, llm node): caller-supplied question +
  file contents, inline Pydantic findings schema, `on_error: retry`.
- **merge tool** (python): reconcile (inputs == findings ∪ unanalyzed),
  render the findings artifact.

## Acceptance Criteria

- [ ] Graph + prompts authored solely via scripts/author.sh with
      authoring report artifact
- [ ] Map-node parallel execution over partitions; per-batch typed
      findings
- [ ] Both modes demonstrated: one exhaustive-audit run and one
      semantic-grep run ("find information related to Q" over docs/,
      needles cited with paths)
- [ ] Reconciliation invariant: every input file appears in findings or
      is listed unanalyzed; no silent drops
- [ ] Demo run against a real corpus partition with demo-output.log
- [ ] Unit tests with `@pytest.mark.req(...)` for partition and merge
      tools
- [ ] README documents the manifest contract and one worked example

## Agent Contract (the sell)

The consumer is an agent at tool-selection time; it matches its current
question against tool descriptions, so the description IS the retrieval
key. Binding presentation requirements:

- **Question-first naming:** the MCP/registry surface presents as
  `semantic_grep` semantics — "Ask a question about a set of files; get
  cited excerpts back; guaranteed nothing skipped" — not as the
  mechanism ("map-node fan-out").
- **Firing moment = the default's failure signature:** the description
  and the FR-853 instruction name the trigger as: grep returned nothing
  (concept, not string), grep returned too much, or the plan says "read
  N files to answer one question."
- **Sell the evidence, not the search:** output is a citable artifact
  (paths + excerpts + coverage guarantee "all N read, K relevant") —
  admissible in FRs and judgements where subagent narrative is not
  (input closure). The reconciliation invariant is the product, not an
  internal detail.

## Alternatives Considered

- **Keep hand-running subagent batches**: sequential, unmerged,
  chat-transient; ×8 in one day already proved the shape.
- **Per-corpus bespoke graphs**: the FR-851 graph is corpus-specific;
  this FR extracts the reusable shape without retiring FR-851's
  (requirement semantics stay specialized).

**Prior art:** `docs/2026-07-29-research-subagent-promotion.md`
recommendation 1 (C1) — filed verbatim after 24 days dormant;
`examples/demos/map/graph.yaml` — node pattern precedent, kept; FR-851
`req_witness_audit` graph — reconciliation discipline reused,
specialized graph kept; `pipeline_audit` / code-analysis agent —
adjacent but corpus-agnostic parametrization distinguishes this FR;
RAG examples (`rag_example`, `tavily_rag`) — kept: embedding retrieval
for large/external corpora, this graph is the exhaustive-read
complement for repo-scale corpora where recall must be total.

## Devil's Advocate (2026-08-22, operator-prompted)

Would FR-855's index suffice? Mostly yes. The enumerable clusters (13 +
10 recurrences) are covered by FR-855/FR-856 at zero LLM cost; the delta
census shows only 2 corpus-ish audits in 3.5 weeks; the one witnessed
novel-question incident (FR-854's prior-art miss) is cured cheaper by
FR-856's mechanical noun search at judge time. The semantic-grep pitch
is one incident away from `growth_as_default`. Disposition: PARKED at
LOW — the two-strike clock restarts now that the environment changed
(adapter migration + FR-855/856 absorb the known demand). Judge this FR
only when an agent hits the firing moment (grep futility / N-file read)
after FR-855 is enforced, and cite that occurrence here.

## Related

- docs/2026-07-29-research-subagent-promotion.md (census, cluster C1)
- feature-requests/FR-851-requirement-witness-audit.md
- feature-requests/FR-853-agent-instrument-registry.md (this graph gets
  a `Task shapes:` row once both land)
