# Research: Subagent Delegation Promotion — Audit-Log Analysis

**Date:** 2026-07-29
**Question:** Should `runSubagent` usage be redirected to graph generation?
When: expected reuse? certain complexity?
**Method:** `read_raw_output_first` — full dump of every subagent launch in
`.github/hooks/logs/audit.jsonl` (FR-414 audit trail), clustered by brief
shape, then judged against the delegation-boundary discriminators from
`docs/diary/diary-2026-07-29-subagent-or-graph-delegation-boundary.md`.

## Data

- **Source:** `.github/hooks/logs/audit.jsonl` (14 MB, all PreToolUse
  invocations). Subagent launches are already fully observed — no new
  instrumentation was needed for this analysis.
- **Population:** 68 launches (`runSubagent` 65, `search_subagent` 2,
  `Agent` 1), 2026-05-21 → 2026-07-28, 19 distinct sessions.
- **Agents:** default 42, `Explore` 26.
- **Not observed in OTel:** FR-759 spans cover `yamlgraph` graph-run/node
  execution only; main-session subagent launches appear nowhere but the
  audit log.
- **Caveat:** the audit `detail` field truncates `tool_input` at 500
  chars — brief *heads* are preserved (agentName, description, first ~400
  chars of prompt), full briefs are not.

## Discriminators applied

From the delegation-boundary reflection (in order of strength):

1. **Contract-shaped output** — deliverable with verifiable structure →
   graph, on first occurrence.
2. **Input closure** — execution must not inherit requester narrative →
   graph, structurally.
3. **Two-strike reuse** — second occurrence of the same brief shape →
   graduate to graph.
4. **Pipeline membership** — inside an enforcement chain → graph
   (traces, audit, Commandment 9).

Complexity is explicitly **not** a discriminator.

## Clusters found

### C1 — Corpus batch analysis (8× in one session, 2026-05-30) → PROMOTE

Eight near-identical briefs in session `3f20a392`: "THOROUGH analysis.
Read every test file listed below…" × {core engine, CLI+process,
integration, safety/provider, linter/validation, early/mid/late FR
tests}. This is a `type: map` fan-out with a `collect:` merge, executed
by hand as eight subagent calls.

- Discriminators hit: contract-shaped (per-partition findings report),
  reuse (any corpus audit: tests, docs, capabilities, diary), two-strike
  ×8 in a single day.
- **Promotion:** generic corpus-analysis graph — input: file-list
  partitions; map node running per-partition analysis; merge node
  assembling a findings artifact. Precedent: `examples/demos/map_demo`,
  `pipeline_audit`, the code-analysis agent.

### C2 — FR claim verification (9× across 6 sessions) → PROMOTE

"I need to judge FR-452…" (05-24), "Research for FR-455/456 judge",
"Gather FR-637/638/639 context" (07-01), FR-642 rejudge context,
"Verify FR-668 through FR-674 claims" (07-03), "Read these 7 FR files"
(07-03), FR-685 spec read (07-05), FR status checks (06-30, 07-02).

The judgement itself was absorbed by the judge-fr adapter (FR-758), and
mechanical status reading by `scripts/fr_board.py` — but **pre-judgement
claim-verification research** still fires as ad-hoc subagents. This is
the exact input-closure violation class: research feeding a judgement
arrives as chat narrative instead of a citable artifact.

- Discriminators hit: input closure (judgement pipeline), contract shape
  (claims → verified/refuted findings), reuse ×9, pipeline membership
  (Plan → Judge chain).
- **Promotion:** a research node in the judge graph, or routing through
  the existing chaplain research step (CAP-113), emitting a findings
  artifact the judgement cites.

### C3 — Precedent / pattern search (7× across 4 sessions) → DATA, NOT A GRAPH

"Find map node graph examples", "Does `type: agent` work inside `map`?",
"Find agent tool registration pattern", "all examples using agent nodes
with tools", "every node_config key used" (×2), "how to implement a new
built-in tool type".

Recurring, but the deliverable is a lookup, not a pipeline. The cheapest
cure is a **generated pattern index** — examples indexed by node
type/feature, sibling to `reference/module-map.md` — regenerated the
same way the module map is. Documenting patterns is cheaper than new
code (the URL-prompt-loading precedent, CLAUDE.md §4).

### C4 — Capability-status queries (~5×) → REGISTRY DISCOVERABILITY

"Is `write_data_file` implemented?", "what memory primitives exist?",
"token/context reporting?", "count examples and demos", "FR-658
graph-as-tool docs". The CAP registry (`capabilities/CAP-*.yaml`)
already answers these; the recurring subagent is a symptom of a
discoverability gap, not missing machinery. Cure sits with C3's index.

### C5 — Project-arc research (novel_fandom, ~6×) → NO ACTION

Canon reviews, genesis context, FR-691/692 infra mapping. Clustered in
one project arc (sessions `bca65748`, `8cdbd670`), arc concluded.
Retroactive promotion would be `growth_as_default`.

### C6 — Genuine one-off exploration → KEEP AS SUBAGENT

Ecosystem survey (06-30), ActiveGraph paper mapping (07-05), safe
mobile/web access research (07-28), genesis-era archaeology (05-23).
Output consumed only by the requesting session; no contract, no
recurrence. This is what `Explore` is for.

## Secondary findings

- **Brief hygiene:** ~30 of 68 launches have an **empty `description`**
  — and description is the natural clustering key for any mechanical
  two-strike detector. A PostToolUse advisory (warn on empty subagent
  description) is a near-zero-cost enabler for future detection.
- **Migration already happened at the enforcement tier:** post-early-July
  the log contains research-only subagents. Judgement, review, and
  authoring delegation all moved to graph adapters (FR-758, review
  graph, FR-765/767). The remaining promotion surface is the research
  tier only.
- **Observation stage of the two-strike detector is free:** every launch
  is already in the audit log with session, timestamp, and brief head.
  The missing pieces are the recurrence query and the advisory surface
  (see Seed in the delegation-boundary diary entry: observe → advise →
  gate).

## Recommendations

| # | Action | Route | Effort signal |
|---|--------|-------|---------------|
| 1 | Corpus-analysis fan-out graph (C1) | Chaplain proposal → FR | 8 hand-run briefs in one day prove the shape |
| 2 | Claim-verification research artifact in judge pipeline (C2) | Chaplain proposal → FR (touches judge graph — judged scope) | 9 recurrences, input-closure class |
| 3 | Pattern index generation (C3+C4) | Chaplain proposal — likely docs/script, not framework code | 12 recurrences across both clusters |
| 4 | Empty-description advisory (hygiene) | Fold into any hooks FR; PostToolUse warn only | Enables mechanical detection |

Non-goals: no PreToolUse *denial* for subagents (research delegation is
legitimate; the gate arc, if ever, starts at observe/advise), no
retroactive promotion of concluded project arcs (C5), no change to
Explore usage for one-offs (C6).
