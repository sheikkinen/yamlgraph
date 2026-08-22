# Feature Request: Subagent-Call Classification Graph (Retrospective Measurement)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Judged 2026-08-22 (APPROVED WITH REVISIONS) — AUTHORITY SUSPENDED:
undispositioned prior art discovered post-judgement (see Prior Art
Disposition below); requires re-judgement or rescope
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

## Prior Art Disposition (discovered 2026-08-22, post-judgement)

**`docs/2026-07-29-research-subagent-promotion.md` — this census was
already run.** Full `read_raw_output_first` dump of every subagent
launch in `.github/hooks/logs/audit.jsonl` (68 launches, 2026-05-21 →
07-28, 19 sessions), clustered into 6 classes with promote/keep
verdicts and a 4-row recommendations table (corpus-analysis fan-out
graph; claim-verification artifact in the judge pipeline; pattern
index; empty-description PostToolUse advisory). Companion discriminators
in `docs/diary/diary-2026-07-29-subagent-or-graph-delegation-boundary.md`.
None of the four recommendations was ever filed as an FR or proposal
(verified by grep 2026-08-22) — the analysis died in the doc.

**Impact on this FR:**

1. The Problem statement's "we have no measurement" is FALSE. A base
   rate exists: post-early-July, enforcement-tier delegation already
   migrated to graph adapters (FR-758/765/767); the residual promotion
   surface is the research tier only.
2. The judgement's R-1 raw-read gate is substantially satisfied by the
   07-29 full-dump analysis; only the 07-28 → present delta window is
   unread.
3. The extraction substrate question is answered: `audit.jsonl` logs
   every `runSubagent` PreToolUse with session, timestamp, and brief
   head (500-char truncation caveat) — not the chronicle session store
   this FR assumed.
4. Per the Sermon (FR-737 rule): a proposal re-entering prior-art
   territory must distinguish itself or die by the same rationale. The
   only distinguishing claims available: (a) mechanized/repeatable vs.
   one-shot manual, (b) 07-28 → present delta. Whether those justify a
   graph, or whether the correct action is to file the four dormant
   07-29 recommendations directly, is the re-judgement question.

**Recorded irony (evidence for FR-853):** this FR is itself the second
firing of the exact investigation it proposes — the 07-29 analysis was
forgotten because no index made it findable at planning time.

## Related

- Companion FR: FR-853 (agent instrument registry + instruction)
- feature-requests/FR-851-requirement-witness-audit.md (pipeline
  precedent)
- docs/2026-07-29-research-subagent-promotion.md (prior census — see
  Prior Art Disposition)
- docs/diary/diary-2026-07-29-subagent-or-graph-delegation-boundary.md
  (delegation discriminators)
- docs/diary/2026-08-22-the-cobblers-children-have-no-graphs.md
- .github/skills/session-introspection/SKILL.md

## Judgement (2026-08-22)

**Verdict:** APPROVED WITH REVISIONS — full judgement in
`feature-requests/FR-854-subagent-call-classification-graph.judgement.md`
(R-1 raw read before authority; R-2 frozen extraction contract; R-3
per-stratum base rates; R-4 graph-registry reconciliation; R-5
committed authoring brief; R-6 mechanical ACs).

**Post-judgement suspension:** the judgement's input set did not include
`docs/2026-07-29-research-subagent-promotion.md`, which already contains
the census this FR proposes. Prior-art disposition is a pre-authority
gate (Sermon, FR-737); authority is suspended until the FR is re-judged
against the disposition above — expected outcomes: REJECT in favor of
filing the four dormant 07-29 recommendations, or rescope to
"mechanize the 07-29 census as a repeatable delta-window graph."
