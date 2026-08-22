# Feature Request: Agent Instrument Registry + is_this_a_graph Instruction

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-22
**First consumer / first event:** every agent session in this repo, at
planning time — the next task whose plan contains "for each item, ask the
model" or a parallel subagent fan-out.

## Summary

Graduate the `is_this_a_graph?` question into `copilot-instructions.md`
with its firing moment, and give agents a task-shape → graph instrument
index so the check has something to match against.

## Value Statement

Agents stop re-implementing map-reduce with terminal loops and subagents
when a registered graph already expresses the task natively.

## Problem

Agents working in this repo never propose yamlgraph as their own
instrument, despite full framework knowledge. Confirmed twice: the
Scripture records `builders_never_call` graphs found unconsumed
(2026-07-17 introspection arc), and on 2026-08-22 the operator had to
point out that parallel LLM analysis — table stakes via the map node —
was never once proposed by the agent
(`docs/diary/2026-08-22-the-cobblers-children-have-no-graphs.md`, trap
named `first_person_tool_horizon`).

The gap is NOT discovery tooling: `yamlgraph graph list` and the MCP
`list_graphs` tool already exist and sit registered in the agent's tool
surface. The gap is (a) no instruction naming the firing moment, and
(b) no task-shape metadata letting an agent match its plan against the
registry. Familiarity is stored under "things I edit," not "things I
wield" — no amount of framework knowledge fixes a categorization that
happens before tool selection runs.

## Ideal Result

An agent whose plan contains an N-items-×-LLM loop, a multi-stage LLM
pipeline, or a parallel analysis fan-out reflexively consults the
instrument index, names the matching graph (or its absence) in one
sentence, and only then falls back to scripts or subagents. The operator
never again has to point at an unused instrument.

## Proposed Solution

1. **copilot-instructions update**: add `is_this_a_graph` to the
   questions canon with firing moment "the instant a plan contains 'for
   each item, ask the model', a multi-stage LLM pipeline, or parallel
   subagent fan-out" — map node is the native map-reduce, race the native
   hedging, router the native dispatch; scripts/subagents are the
   fallback, not the default. Second witnessed recurrence of
   `builders_never_call` justifies graduation per the two-strike process.

2. **Instrument index**: task-shape → graph mapping surfaced where the
   agent already looks (graph metadata consumed by `graph list` /
   MCP descriptions), e.g. "N items × LLM call" → map pattern
   (`examples/demos/map_demo`), "hedged generation" → `race_demo`,
   "root-cause chain" → `five_whys`, "structured ideation" →
   `innovation_matrix`. No new top-level directory: a folder without a
   named reader and firing moment is archived at birth
   (`who_reads_this_when`).

## Acceptance Criteria

- [ ] `copilot-instructions.md` questions canon gains `is_this_a_graph`
      with its firing moment and the two recurrence citations
- [ ] Instrument index exists in graph metadata or a single reference
      table reachable from the instruction (one hop, no new folder)
- [ ] At least 5 task shapes mapped to existing registered graphs
- [ ] Diary entry cross-references updated (graduation recorded)

## Alternatives Considered

- **New `agent-graphs/` folder**: rejected — discovery tooling already
  exists; location was never the gap, the firing instruction was.
- **Do nothing / rely on memory notes**: user-memory note exists but is
  agent-instance-scoped; doctrine must live in the repo.
- **Live interception of subagent calls**: separate FR (subagent-call
  classification, measurement-first); premature here.

**Prior art:** `builders_never_call` (Scripture questions canon, found
unconsumed 2026-07-17) — this FR is its graduation vehicle, not a
duplicate; `does_the_tool_fit_or_merely_exist` (Scripture) — same family,
this FR supplies the fit-check moment; MCP graph registration (CAP-19) —
kept as-is, this FR adds the instruction layer above it. Disposition:
build on all three, supersede none.

## Related

- docs/diary/2026-08-22-the-cobblers-children-have-no-graphs.md
- .github/copilot-instructions.md (questions canon)
- yamlgraph/mcp_server.py (CAP-19 graph registration)
- Companion FR: FR-854 (subagent-call classification graph)
