# Judgement: FR-853 Agent Instrument Registry + is_this_a_graph Instruction

**Prior art:** FR-853-agent-instrument-registry.md is the FR under
judgement, not prior art — self-match on filename nouns; no disposition
required beyond this judgement itself.

**Verdict:** APPROVED WITH REVISIONS - The problem is real and the proposed remedy is strategically aligned, but authority activates only after the FR resolves its graduation-threshold contradiction, freezes one instrument-index surface, and corrects the cited graph names/paths.

**Reviewed against:** `feature-requests/FR-853-agent-instrument-registry.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `docs/diary/2026-08-22-the-cobblers-children-have-no-graphs.md`; `.github/copilot-instructions.md`; `yamlgraph/discovery.py`; `yamlgraph/export/mcp.py`; `capabilities/CAP-19-mcp-server-interface.yaml`; `examples/demos/map/graph.yaml`; `examples/demos/fan-out/graph.yaml`; `examples/demos/race/graph.yaml`; `examples/demos/five-whys/graph.yaml`; `examples/demos/innovation_matrix/graph.yaml`; `examples/demos/router/graph.yaml`.

## What is sound

The FR names a concrete first consumer and event: repo agents at planning time when a plan contains an LLM loop or parallel subagent fan-out (`feature-requests/FR-853-agent-instrument-registry.md:8-10`). The problem is evidenced rather than merely asserted: the diary records registered graph tools and graphs sitting unused while the agent reaches for terminal loops, subagents, or bespoke scripts (`docs/diary/2026-08-22-the-cobblers-children-have-no-graphs.md:11-18`), and it distinguishes forced compliance from first-person proposal in the FR-851 arc (`docs/diary/2026-08-22-the-cobblers-children-have-no-graphs.md:20-25`).

The proposed shape fits existing doctrine. The current questions canon already includes tool-fit questions (`.github/copilot-instructions.md:119-132`) and graph-backed generative methods (`.github/copilot-instructions.md:134-145`), so adding `is_this_a_graph` is pattern documentation / agent operating doctrine, not a new framework primitive. The existing MCP/discovery path already carries graph descriptions: discovery reads `name` and `description` from graph YAML (`yamlgraph/discovery.py:194-228`), and MCP list/typed-tool surfaces expose those descriptions (`yamlgraph/export/mcp.py:176-218`, `yamlgraph/export/mcp.py:258-266`). CAP-19 already establishes graph listing and invocation over MCP (`capabilities/CAP-19-mcp-server-interface.yaml:9-24`).

## Required revisions

### R-1: Resolve the graduation-threshold contradiction

Amend the FR and cited diary so they agree on why this is ready for Scripture. The FR says the second witnessed recurrence justifies graduation (`feature-requests/FR-853-agent-instrument-registry.md:52-58`), while the diary says the second recurrence is a candidate and "a third firing graduates it" (`docs/diary/2026-08-22-the-cobblers-children-have-no-graphs.md:57-58`). Fold in the repo process rule exactly: "Heuristic appears twice -> create FR; confirmed recurrence -> graduate to Scripture" (`.github/copilot-instructions.md:147-149`). The revised FR must state whether the 2026-08-22 case is the confirmed recurrence that authorizes graduation now; if yes, update the diary cross-reference to remove the third-firing conflict.

### R-2: Freeze the instrument-index surface to graph description metadata

Replace the "graph metadata or a single reference table" alternative (`feature-requests/FR-853-agent-instrument-registry.md:73-74`) with one implementation contract: existing graph YAML `description` metadata gains a literal `Task shapes:` clause, and `.github/copilot-instructions.md` tells agents to consult the existing graph list/MCP discovery surface for that clause. This uses the already-consumed description field (`yamlgraph/discovery.py:194-228`) and avoids a new reference table, new top-level directory, or new discovery command.

### R-3: Correct the graph names and paths before enforcement

Replace the inaccurate example names/paths in the FR. The registered map graph is `examples/demos/map/graph.yaml` with `name: map-demo` (`examples/demos/map/graph.yaml:4-6`), not `examples/demos/map_demo`; the race graph is `examples/demos/race/graph.yaml` with `name: race-demo` (`examples/demos/race/graph.yaml:5-7`), not `race_demo`. Freeze at least these existing registered targets for the first index: `map-demo`, `fan-out-demo`, `race-demo`, `five-whys`, `innovation-matrix`, and `tone-router-demo` (`examples/demos/fan-out/graph.yaml:6-8`; `examples/demos/five-whys/graph.yaml:4-6`; `examples/demos/innovation_matrix/graph.yaml:1-3`; `examples/demos/router/graph.yaml:4-6`).

### R-4: Add a mechanical witness for discovery visibility

Revise the acceptance criteria so the enforcer must add or update a test proving at least one `Task shapes:` description survives `discover_graphs()` and the MCP list output. The current ACs check that text exists, but not that the agent-visible discovery surface actually carries the index (`feature-requests/FR-853-agent-instrument-registry.md:69-76`; `yamlgraph/export/mcp.py:258-266`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `.github/copilot-instructions.md` questions canon entry for `is_this_a_graph` |
| D-2 | Existing graph YAML `description` metadata for `examples/demos/map/graph.yaml`, `examples/demos/fan-out/graph.yaml`, `examples/demos/race/graph.yaml`, `examples/demos/five-whys/graph.yaml`, `examples/demos/innovation_matrix/graph.yaml`, and optionally `examples/demos/router/graph.yaml` |
| D-3 | `docs/diary/2026-08-22-the-cobblers-children-have-no-graphs.md` cross-reference/graduation status |
| D-4 | Targeted discovery/MCP-list test coverage for the `Task shapes:` visibility contract |

Not authorized: new top-level documentation or registry directories; new graph files or prompt files; live interception of subagent calls or PreToolUse nudges; new MCP tools; changes to graph execution semantics; implementation of companion FR-854.

## Revised acceptance criteria

- [ ] AC-01: `.github/copilot-instructions.md` contains an `is_this_a_graph` questions-canon entry with the firing moment "the instant a plan contains 'for each item, ask the model', a multi-stage LLM pipeline, or parallel subagent fan-out" and cites both recurrence witnesses.
- [ ] AC-02: `docs/diary/2026-08-22-the-cobblers-children-have-no-graphs.md` cross-references FR-853 and no longer contradicts the FR's graduation threshold.
- [ ] AC-03: At least five existing registered graph descriptions contain a literal `Task shapes:` clause mapping a task shape to the graph; the first set includes `map-demo`, `fan-out-demo`, `race-demo`, `five-whys`, and `innovation-matrix`.
- [ ] AC-04: A targeted test proves `Task shapes:` text is returned through `discover_graphs()` and the MCP `yamlgraph_list_graphs` payload.
- [ ] AC-05: The implementation creates no new registry directory, no new MCP tool, and no live interception/nudge mechanism.
- [ ] AC-06: Any touched graph YAML files pass the existing graph lint path required for graph-artifact edits.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-4 into the FR before implementation authority activates. | GATE |
| C-2 | If graph YAML descriptions are edited, use the governed graph-authoring route required by repo doctrine for material graph artifact changes. | GATE |
| C-3 | Treat the `.github/copilot-instructions.md` doctrine change as requiring human review before merge. | GATE |
| C-4 | Preserve CAP-19 discovery/list behavior; the index must ride existing descriptions unless a later FR authorizes a schema/API change. | GATE |
| C-5 | Do not implement FR-854 or any live subagent-call classifier in this FR. | GATE |

Authority granted: after the required revisions are folded into the FR, enforcement may add the `is_this_a_graph` instruction, surface task-shape hints through existing graph descriptions, update the diary cross-reference, and add the targeted discovery/MCP visibility witness.
