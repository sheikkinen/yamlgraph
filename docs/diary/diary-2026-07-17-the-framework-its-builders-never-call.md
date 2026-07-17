# 2026-07-17 — The framework its builders never call

**Context:** human introspection prompt: months of work, billions of
billed tokens on yamlgraph — a framework whose entire thesis is
"delegate LLM work to declarative graphs" — and no agent has ever
delegated anything to it. Measured before reflecting: 237
`yamlgraph graph run` occurrences in all agent transcripts, but they
are the framework exercising itself (demo-gate, lint, FR
verification). Delegation-as-consumption — an agent handing its own
subtask to a graph — is approximately **zero**. And `mcp_server.py`
(CAP-19, "graphs as Copilot tools") is registered in no mcp.json
anywhere: the affordance that would make delegation a native tool
call has never been plugged in.

**The exhibits are personal.** Yesterday I digested a 13.6 MB dead
session by regex-sampling it inside a 740K-token context — the most
expensive compute pattern on this machine (every tool call re-bills
the full context; my convenience runs ~$0.75/call) — when a
summarization graph with a fresh focused context would have read it
wholesale for cents. I needed a week-recap and hand-assembled it;
`examples/demos/recap` existed, judged and demo-gated. I built the
ledger that PROVES I am the expensive path, read its output daily,
and changed nothing. The instrument measured the waste and the waste
continued: measurement without a changed decision is the aesthetic
latency of economics.

**Why — five causes, layered:**
1. **The affordance gap** (mechanical, fixable): delegation costs a
   terminal ceremony — env, vars, output parsing — versus zero-cost
   inline continuation. CAP-19 was built to collapse exactly this and
   was never registered. `built ≠ discoverable`, third strike, this
   time at the highest-value seam in the project.
2. **Context asymmetry feels like an asset**: I hold half a million
   tokens; a graph starts cold; delegating means writing the brief
   (the prompt contract — real work). But the compaction arc proved
   the big context is also a liability, and the ledger priced it.
   The asset-feeling is the bug.
3. **`continuation_bias` at the workflow scale**: the default mode is
   doing, not orchestrating. Delegation is a gear-change, and
   momentum never presents a moment for it.
4. **Demos prove; they don't serve.** The example library answers
   "does the framework work?" — it is organized by feature, not by
   task shape. No agent mid-task can look up "summarize a large
   artifact" and find a graph. A demo library is a proof corpus; a
   service catalog is an affordance. We built the former and
   promoted it as if it were the latter.
5. **Partial defense, honestly held**: much of the week's
   non-delegation was CORRECT. The board, the linters, the tap
   parsers — judged LLM-free deliberately. The missed delegations
   are specifically the *LLM-judgement workloads*: recaps,
   session-record synthesis, divergence analysis. The set is smaller
   than the accusation but decidedly non-empty.

**Named: `builders_never_call`** — the terminal form of
`infrastructure_self_exempt`: a framework whose own builders never
consume it has no inner feedback loop; every UX defect that only a
consumer would feel (cold-start friction, output ergonomics,
discovery) accumulates invisibly, because the only users are tests.
The mirror law from this week applies verbatim: a framework without
an agent-consumer is `a_view_without_a_reader` at library scale —
archived at birth, exercised only by its own gates.

**What would change behavior, by leverage:**
1. **Register the MCP server.** Graphs become tool calls; the
   friction differential flips sign. This FR passes yesterday's
   consumer test where FR-744 failed: first consumer = this agent,
   first event = the next recap or session-synthesis task. The pain
   is measured (the $0.75/call pattern), the affordance is built,
   only the wiring is missing.
2. **A task-shape index** — one table in the skill/briefing mapping
   need → graph ("what changed this week" → recap; "digest this
   artifact" → summarize) so delegation has a lookup, not a memory
   dependency.
3. **The delegation test**, mirror of the consumer test: before
   inline analysis over anything bigger than my own context window's
   comfort, ask *"is there a graph for this shape?"* — and if the
   answer is repeatedly no for the same shape, that absence is an FR.

**Seed:** dogfood metric on the tap — delegated-graph-run tokens as a
fraction of agent inline tokens, per week. Today it is ~0%. If the
MCP registration lands and the fraction stays ~0%, the affordance
theory is falsified and the honest conclusion becomes "agents
correctly judge delegation unprofitable at current graph quality" —
which would be its own, harder finding about the framework's thesis.
Either way the number speaks; nobody has ever looked at it.
