# Feature Request: Subagent-Call Classification Graph (Retrospective Measurement)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-22
**First consumer / first event:** the doctrine itself — the report either
justifies a live-redirect mechanism FR with real numbers or kills it
cheaply. First event: first run against this workspace's session history
after enforcement.

## Summary

A yamlgraph graph that retrospectively classifies past agent subagent
invocations and LLM loops as graph-shaped vs. genuinely agentic,
producing the base rate that any future interception mechanism must cite.

## Value Statement

The decision "should subagent calls be redirected to graphs?" gets made
on measured session history instead of intuition — and the measurement
instrument itself dogfoods the map-reduce pattern under study.

## Problem

We suspect a large fraction of `runSubagent` invocations and terminal
LLM loops are graph-shaped work (map-reduce, hedging, routing) that
yamlgraph expresses natively — but we have no measurement. Building an
interception/auto-redirect mechanism first would tax every subagent call,
collide with the FR-767 sole-route authoring doctrine (auto-generated
graphs still require author.sh + lint + smoke), and risk misrouting
exploration tasks. Measure before mechanize.

Context: `docs/diary/2026-08-22-the-cobblers-children-have-no-graphs.md`
(`first_person_tool_horizon`); operator direction 2026-08-22.

## Raw Output Read (measurement / metric-tooling FRs only)

To be completed at enforcement, before any aggregate is computed:

- **Samples read:** >= 10 raw subagent prompts extracted from the session
  store, dumped to `tmp/fr854-raw-samples/` and read end-to-end.
- **What I saw:** one concrete, surprising detail per sample, cited in
  the evidence file. The judge withholds authority for the report stage
  until this section shows substance (Scripture, `read_raw_output_first`).

## Ideal Result

One command runs a graph over this workspace's recorded subagent
invocations and emits a ranked report: X% matched an existing registered
graph (named), Y% were tailored-graph candidates (task shape named), Z%
genuinely agentic. The Tier-3 question ("automatic redirect?") is
answered by a number, not a debate — and the instrument index (FR-853)
gets its task-shape vocabulary from the observed clusters.

## Proposed Solution

A yamlgraph graph, authored via the governed route (`scripts/author.sh`):

1. **Extract** (python tool): pull past subagent prompts / LLM-loop
   invocations from the local session store (`sessions`/`turns` tables;
   `scripts/vscode/` introspection precedent — see the
   session-introspection skill).
2. **Classify** (map node, haiku-class model): fan out over extracted
   calls; each classified `graph-shaped-existing` (matched registered
   graph named) | `graph-shaped-novel` (tailored-graph candidate, task
   shape named) | `genuinely-agentic` (open-ended tool use required).
   Inline Pydantic schema; boundary reconciliation per FR-851 precedent:
   hallucinated ids rejected and requeued, duplicates keep first,
   audited ∪ unaudited == inputs.
3. **Report** (python tool): ranked report — % per class, top recurring
   graph-shaped task shapes, named existing graphs that would have
   served. Partition by cause stratum before any ranking is treated as a
   worklist (FR-851 lesson: an audit over joined data audits the join).

```bash
yamlgraph graph run examples/demos/subagent_census/graph.yaml --full
```

## Acceptance Criteria

- [ ] Graph authored via scripts/author.sh with authoring report artifact
- [ ] Runs against real session history, not fixtures
- [ ] Raw Output Read section completed with >= 10 cited samples
- [ ] Reconciliation invariant holds: every extracted call is classified
      or listed unclassified; no silent drops
- [ ] Report names matched existing graphs per `graph-shaped-existing`
      verdict
- [ ] Tests added (unit: extraction, reconciliation, report rendering)
- [ ] Evidence file in feature-requests/evidence/ with class distribution

## Explicitly Deferred (Tier 3 — out of scope)

Automatic redirect of live subagent invocations to graphs, and on-the-fly
tailored-graph generation. These earn an FR only if this measurement
shows a substantial graph-shaped fraction; a synchronous classifier in
the hot path is premature without that number.

## Alternatives Considered

- **Live PreToolUse classifier on runSubagent**: rejected for now —
  latency tax on every call, no base rate to justify it.
- **Manual review of session history**: does not scale past a handful of
  sessions and produces no reproducible artifact.
- **Python script instead of a graph**: rejected on principle — this FR
  exists because scripts-first is the trap under study.

**Prior art:** FR-851 requirement-witness audit — same
extract→map-classify→reconcile→report shape; this FR reuses its
reconciliation discipline over a different corpus, superseding nothing.
Chronicle/session-store tooling (`session_store_sql`,
`scripts/vscode/now.py`) — kept as the extraction substrate.

## Related

- Companion FR: FR-853 (agent instrument registry + instruction)
- feature-requests/FR-851-requirement-witness-audit.md (pipeline
  precedent)
- docs/diary/2026-08-22-the-cobblers-children-have-no-graphs.md
- .github/skills/session-introspection/SKILL.md
