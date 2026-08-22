# Feature Request: Agent Instrument Registry + is_this_a_graph Instruction

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS (2026-08-22), revisions folded
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
   fallback, not the default.

   **Graduation threshold (R-1 resolution):** per the Scripture process
   rule ("Heuristic appears twice → create FR; confirmed recurrence →
   graduate to Scripture"), the first recurrence is the Scripture's own
   `builders_never_call` record (2026-07-17), the second — confirmed —
   recurrence is the 2026-08-22 operator-witnessed case. This FR is the
   graduation vehicle and its enforcement performs the graduation now;
   the diary's "a third firing graduates it" line is superseded and the
   diary cross-reference is updated in scope (D-3) to remove the
   contradiction.

2. **Instrument index (R-2 frozen surface)**: existing graph YAML
   `description` metadata gains a literal `Task shapes:` clause, and
   `.github/copilot-instructions.md` tells agents to consult the
   existing graph list / MCP discovery surface for that clause. This
   rides the already-consumed description field
   (`yamlgraph/discovery.py` → `yamlgraph/export/mcp.py`); no new
   reference table, no new top-level directory, no new discovery
   command (`who_reads_this_when`).

   **First index targets (R-3 corrected names/paths):** `map-demo`
   (`examples/demos/map/graph.yaml`), `fan-out-demo`
   (`examples/demos/fan-out/graph.yaml`), `race-demo`
   (`examples/demos/race/graph.yaml`), `five-whys`
   (`examples/demos/five-whys/graph.yaml`), `innovation-matrix`
   (`examples/demos/innovation_matrix/graph.yaml`), and optionally
   `tone-router-demo` (`examples/demos/router/graph.yaml`).

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: `.github/copilot-instructions.md` contains an
      `is_this_a_graph` questions-canon entry with the firing moment
      "the instant a plan contains 'for each item, ask the model', a
      multi-stage LLM pipeline, or parallel subagent fan-out" and cites
      both recurrence witnesses.
- [ ] AC-02: `docs/diary/2026-08-22-the-cobblers-children-have-no-graphs.md`
      cross-references FR-853 and no longer contradicts the FR's
      graduation threshold.
- [ ] AC-03: At least five existing registered graph descriptions
      contain a literal `Task shapes:` clause mapping a task shape to
      the graph; the first set includes `map-demo`, `fan-out-demo`,
      `race-demo`, `five-whys`, and `innovation-matrix`.
- [ ] AC-04: A targeted test proves `Task shapes:` text is returned
      through `discover_graphs()` and the MCP `yamlgraph_list_graphs`
      payload (R-4 mechanical witness).
- [ ] AC-05: The implementation creates no new registry directory, no
      new MCP tool, and no live interception/nudge mechanism.
- [ ] AC-06: Any touched graph YAML files pass the existing graph lint
      path required for graph-artifact edits.

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

## Judgement (2026-08-22)

**Verdict:** APPROVED WITH REVISIONS — full judgement in
`feature-requests/FR-853-agent-instrument-registry.judgement.md`.
Revisions R-1 (graduation-threshold resolution), R-2 (index surface
frozen to `Task shapes:` in graph descriptions), R-3 (graph names/paths
corrected), and R-4 (discovery/MCP visibility witness) are folded above.

**Scope frozen:** D-1 copilot-instructions questions-canon entry; D-2
`Task shapes:` clauses in the six named demo graph descriptions; D-3
diary cross-reference/graduation status; D-4 targeted discovery/MCP-list
test. Not authorized: new directories/registries, new graph or prompt
files, live interception or PreToolUse nudges, new MCP tools, execution
semantics changes, any FR-854 implementation.

**Gates:** C-1 revisions folded before authority (done above); C-2
graph description edits go through the governed authoring route; C-3
copilot-instructions change requires human review before merge; C-4
CAP-19 discovery/list behavior preserved; C-5 no FR-854 work here.

### Questions for the human

None — revisions were mechanically foldable.
