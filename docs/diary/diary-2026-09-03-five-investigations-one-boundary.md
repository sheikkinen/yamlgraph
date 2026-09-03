# Diary: Five Investigations, One Boundary

**Date:** 2026-09-03
**Trigger:** "reflect where does it lead to? defined yamlgraph boundary" —
after a session that independently ran five unrelated audits: business
use-case ranking, voicebot opportunities, design-pattern applicability, a
repo-wide tool-definition census, and MCP viability (server, then client,
then `session.create_message()` specifically).

## Where it leads

Every one of the five, approached from a different angle with no shared
premise going in, converged on the same line:

> **YAMLGraph does typed reasoning over an input that is fully known at
> authoring time, invoked by something else that owns discovery, lifecycle,
> and protocol.**

- **Business use cases:** the defensible position is the governed pipeline
  and its evidence, not the runtime as a product — verticals are
  configuration around a fixed census/reduce core, not new topology.
- **Voicebot:** `reference/patterns/fsm-as-conductor.md` names it outright —
  "statemachine-engine owns lifecycle; YAMLGraph owns cognition." The
  Discord/PSTN research arc rediscovered this the hard way and called it
  `infrastructure_gravity` — work migrates to where the tools already are,
  even when the center of gravity is elsewhere.
- **Design patterns:** Game Loop/ECS as a node type is doctrine-blocked by
  the same FSM-as-conductor line; Decorator-as-YAML is blocked by a
  separate, older ruling that cross-cutting concerns belong at the compiler
  boundary, not per-node YAML. Both rejections are the boundary enforcing
  itself in a different vocabulary.
- **Tool census:** graphs hand-roll 91% of their tool declarations rather
  than discovering shared ones at runtime — because a graph's tool needs
  are fixed at authoring time. There is no dynamic-discovery problem here to
  solve; the one narrow place it exists (`manifest:`, FR-768) is a static
  YAML pointer, not a live handshake.
- **MCP:** retired twice — the server direction (FR-910) and the
  client-shaped precedent (A2A's `contrib/a2a_client.py`) — for the same
  reason stated two different ways: no consumer needed yamlgraph to
  *discover* or *be discovered* at runtime, because nothing about a compiled
  graph is open-ended enough to need that. `session.create_message()`
  compounds it: even the one live wire yamlgraph had into "borrow the host's
  model at runtime" was cut same-day as "a solution seeking a problem"
  before the surface it depended on was cut again in August.

## The insight, not just the finding

The interesting fact isn't any single verdict — it's that five investigations
with no shared method landed on one sentence. That's not five independent
opinions; it's five independent measurements of the same boundary from
different instruments, which is much stronger evidence that the boundary is
real and load-bearing than any one audit could produce alone. A framework
that keeps getting pulled toward "own more of the runtime" (lifecycle,
protocol, discovery, transport) and keeps getting pushed back to the same
narrow core by unrelated audits has a boundary worth trusting, not
re-litigating from scratch each time.

## The trap this names

Every one of the five times, the boundary was discovered *after* someone
had already sunk real design or implementation effort into crossing it
(FR-082's sampling backend built and shipped before being dropped; the
Discord/voice evening of architecture before the self-critique; FR-219
approved four months ago with no consumer yet). The boundary is correct but
reactive — it gets enforced by post-hoc audit, never by a pre-hoc gate. Call
this **boundary_rediscovered_by_autopsy**: the cure exists
(`fsm-as-conductor.md`, `is_this_a_graph`, `would_you_use_this`) but nothing
stops a new FR from re-crossing the same line before someone notices, again,
after the fact.

## Seed

If the same one-sentence boundary keeps getting rediscovered by autopsy
across business, pattern, tooling, and protocol audits alike, is it worth
promoting from "documented in `fsm-as-conductor.md`" to a literal judge-time
check — a question the judge doctrine asks of every FR by construction:
*does this proposal make yamlgraph own discovery, lifecycle, or protocol
that something else already owns, or does it keep yamlgraph's contribution
to typed reasoning over a known input?* Five autopsies is enough to graduate
the question; is it enough to graduate the gate?
