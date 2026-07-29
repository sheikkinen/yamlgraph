# 2026-07-29 — Subagent or Graph: The Delegation Boundary

**Prompt from operator:** should subagent usage be redirected to graph
generation? When expected reuse? Certain complexity?

**The repo already answered this three times.** judge-fr (FR-758),
review-pr, and graph-authoring (FR-765/767) each began as prompt- or
subagent-shaped delegation and each was mechanized into a graph adapter
after the same two failure classes: **input closure violations** (chat
narrative leaking into an execution that claimed independence) and
**unverifiable output** (trusting a returned message instead of
verifying an artifact). The migrations were not driven by complexity —
judge-fr is a single LLM call with a rubric. They were driven by
*contract shape*: the moment the deliverable had required headings, a
verdict taxonomy, or a proof artifact, the subagent route could no
longer be audited and the graph route could.

**Discriminators that hold** (in order of strength):

1. **Contract-shaped output.** If the deliverable is an artifact with a
   verifiable structure (report with required sections, verdict, file
   set that must lint), it should already be a graph. A subagent's
   single opaque return message cannot be contract-checked; a graph's
   artifact can — `author.sh` verifies headings and listed paths by
   existence, never by exit code. Contract shape is the tell, not a
   threshold to argue about.
2. **Input closure requirement.** If the execution must NOT inherit the
   requesting session's narrative (judgement, review, authoring), the
   subagent route is structurally wrong: `runSubagent` briefs are
   composed from live chat context by the very session that must be
   excluded. Graphs take a task file and committed artifacts — closure
   is mechanical, not promised.
3. **Expected reuse — the two-strike rule.** The first occurrence of a
   delegation is legitimately a subagent: cheap, exploratory, zero
   ceremony. The *second time the same brief shape is written*, that is
   the graduation trigger (same law as heuristic→FR→Scripture, same law
   as `two_strike_split`). A brief written twice is a prompt template
   begging to be committed as `prompts/*.yaml`.
4. **Pipeline membership.** If the delegation sits inside an
   enforcement chain (chaplain, watcher, CI remediation), it needs
   traces, route logs, and audit entries — graph territory by
   Commandment 9.

**Complexity is NOT a discriminator.** A complex one-off exploration
("map every FSM incident in the diary and tell me what it means") is
still subagent territory: the output is *context for this session*, not
an artifact for the repo. A trivial recurring task (diary indexing) is
graph territory despite being simple. Ranking by complexity would be
`inventory_by_visibility` again — mass instead of incident structure.

**What legitimately remains subagent:** one-off research and
exploration whose deliverable is consumed only by the requesting
session and dies with it. That is what the Explore agent is for. The
moment the deliverable outlives the session, it is an artifact, and
artifacts have a route.

**Trap named:** `delegation_by_convenience` — the activation-energy
asymmetry. A subagent is one tool call; the graph route needs a brief
file and an adapter run. That surface cost biases toward the ephemeral
route even when the artifact class demands the durable one — the exact
mechanism as strike 1's "mv" framing, where a cheap verb hid an
authoring event. The cure is the same as FR-767's: classify by artifact
class and contract shape, never by the cost of the invocation.

**Fresh evidence (today):** the AC-11 replay — "create a graph for
chinese horoscope" — ran through `scripts/author.sh` post-FR-767 and
produced `examples/demos/chinese-horoscope/` with a verified
`tmp/draft-authoring-report.md` (precedent: FR-201 horoscope, map
fan-out). The route that a subagent bypassed yesterday was the route
that worked today. Delegation through the graph did not lose capability;
it gained a precedent citation, a lint record, and a smoke log that a
subagent return message never carries.

**Heuristic:** *second_brief_becomes_graph* — subagent on first
occurrence; on the second occurrence of the same brief shape, author a
graph through the sole route. Contract-shaped or closure-requiring
deliverables skip straight to the graph on first occurrence.

**Seed:** the two-strike trigger currently relies on the agent
remembering its first brief — exactly the kind of memory sessions don't
have. Should PreToolUse *observe* (not deny) `runSubagent` calls,
hashing brief shapes into the audit log, so recurrence detection is
mechanical: "this is the second time this delegation shape has run —
author a graph"? That would give delegation the same graduated
enforcement arc authoring got: observe → advise → gate.
