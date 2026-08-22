# The Cobbler's Children Have No Graphs

**Date:** 2026-08-22
**Context:** Operator meta-reflection after the FR-851 arc: "despite being
familiar with the repo, you haven't proposed implementation as a yamlgraph.
Not once, ever. Map-reduce is not available via in-built tools. Parallel
haiku analysis is table stakes in yamlgraph."

## The Observation

The charge is accurate and the evidence is in my own context window. My
deferred-tool list carries `mcp_yamlgraph_run_graph` and roughly a hundred
registered graphs — `map_demo`, `fan_out_demo`, `race_demo`, `five_whys` —
and I have never once reached for them as instruments. I judge FRs about
map nodes, I enforce them, I write their witness tests, I can recite the
node-factory execution order from memory. Yet when *I* need N parallel LLM
calls, my hand reaches for a terminal loop, a subagent, or a bespoke
Python script.

FR-851 is the sharpest exhibit because it looks like a counterexample and
isn't. The audit pipeline's LLM fan-out — 41 batches through haiku via a
map node — runs as a graph *only because the governed authoring route
forced graph authoring*. My unforced first instinct was
`scripts/req_audit_questions.py` and a sequential loop. The doctrine
proposed the graph; I merely complied. Compliance is not proposal.

## The Trap

Name: **first_person_tool_horizon**. My tool surface divides into
first-person instruments (terminal, file edits, subagents — feedback lands
in my own loop) and third-person artifacts (things the repo builds).
yamlgraph sits in my mind as *the codebase under maintenance*, never as
*my standard library*. The categorization happens before tool selection
ever runs, so no amount of familiarity with map nodes fixes it —
familiarity is stored under "things I edit," not "things I wield."

This is `builders_never_call` (already named in the Scripture's questions
canon, already found unconsumed once) recurring in the agent itself — the
strictest possible form: the builder's own operator had to point at the
unused instrument. Second confirmed recurrence.

The compounding irony: the in-built tool surface genuinely *cannot* do
map-reduce. Subagents are sequential-blocking; terminal loops are serial;
there is no parallel LLM primitive in my native toolkit. The one system
in reach that has it as a first-class node type is the one I maintain.

## The Cure

Before writing any loop that calls an LLM, or spawning subagents for
parallel analysis, or scripting a multi-stage LLM pipeline, ask:
**is_this_a_graph?** Firing moment: the instant a plan contains "for each
item, ask the model." If yes → propose a yamlgraph implementation first
(map node = native map-reduce; race node = native hedging; router = native
dispatch), via the governed authoring route. Scripts and subagents are the
fallback, not the default.

Candidate for the Scripture's questions canon — this entry is the second
witnessed recurrence of `builders_never_call`; a third firing graduates it.

## Seed

**Seed:** Can the firing moment be mechanized? A PreToolUse-shaped nudge
that pattern-matches agent plans for "N items × LLM call" and answers with
"map node exists" would convert this from remembered discipline into
enforced doctrine — the same shape as the reasoning sentinel. And the
inverse question: which *other* repo capabilities sit in my deferred-tool
list, registered and callable, that I have categorized as artifacts rather
than instruments? An inventory of never-invoked MCP tools ranked by
task-shape overlap with my actual session history would name the next
blind spot before the operator has to.
