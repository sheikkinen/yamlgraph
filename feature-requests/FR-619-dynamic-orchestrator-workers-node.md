# Feature Request: Dynamic Orchestrator-Workers Node

**Priority:** LOW
**Type:** Feature
**Status:** Judged — Authority GRANTED as DEFERRED design; build gated on proven need (2026-06-28)
**Effort:** 4 days
**Requested:** 2026-06-28

## Summary

A node where an orchestrator LLM *dynamically* decomposes a task into an
unknown-at-author-time number of subtasks, dispatches each to a worker (clean
context window), and synthesizes the distilled results — the orchestrator-workers
pattern, as opposed to `map` which requires a predefined list.

## Value Statement

Graph authors can express tasks whose shape is unknown until runtime ("change
however many files the task requires", "research across however many sources are
relevant") without hardcoding the fan-out — the orchestrator decides.

## Value Proposal

- **Covers the one workflow YAMLGraph can't express**: `map` fans out over a
  *known* list; this fans out over a list the model *produces*. That is the
  qualitative gap between parallelization and orchestrator-workers.
- **Context isolation by construction**: Each worker runs in a clean window and
  returns a 1–2k-token distilled summary; the orchestrator never sees the workers'
  raw context. This is the sub-agent architecture applied as a graph primitive.
- **Builds on owned pieces**: dynamic subtask generation = one structured LLM
  call; worker execution = existing `subgraph`/`shared-graph-invocation`;
  synthesis = one more LLM call. Mostly composition of existing capabilities.

## Why Deferred

Per Scripture — *"add agency only when it demonstrably helps"* — this is the most
*agentic* and least *predictable* of the 2026 gaps, and it leans toward the
opaque-framework failure mode Anthropic warns against. It should wait until a
concrete graph in this repo provably needs runtime decomposition that `map`,
`copilot`, and `subgraph` cannot express. This FR records the design so the need,
when it arrives, meets a ready plan rather than a blank page.

**Trigger to promote to HIGH:** a real example graph (committed under
`examples/`) where the number of subtasks cannot be known until an LLM inspects
the input, and `map` + `subgraph` demonstrably cannot express it.

## Judgement (2026-06-28)

**Verdict: Authority GRANTED as DEFERRED design — do NOT build yet.** Exemplary deferral: the FR
names its own promotion trigger and flags the strongest alternative against itself. It correctly
invokes the Scripture — *"add agency only when it demonstrably helps"* — and this is the most
agentic, least predictable of the five gaps, leaning toward the opaque-framework failure mode.

**Correction 1 (PRIMARY — elevate "evaluate before building" from advice to a hard gate).** The FR
lists "`map` over an LLM-produced list" as the closest existing path and says to evaluate it first.
Make that a **blocking precondition**: no authority to build the `orchestrator` node until a
committed graph under `examples/` demonstrates that `map` + `subgraph` + `copilot` **cannot** express
the runtime decomposition. Until that example exists, the correct deliverable is a documented recipe
(llm emits typed `list[Subtask]` → map over it → synthesize), not a new primitive. This is the
framework-costume guard made mechanical: prove the cheaper composition fails before adding agency.

**Correction 2 (secondary — keep the empty-plan discipline).** The AC already requires an empty plan
to raise rather than silently pass (FR-598-safe) — retain that exactly; it is the difference between
a typed orchestrator and an unbounded fan-out.

**Frozen scope.** Stays DEFERRED; the design is recorded so the need, when it arrives, meets a plan.
Authority to build is conditioned on a committed example proving `map`+`subgraph`+`copilot`
insufficient. No code until then.

## Problem

YAMLGraph can route (`router`), parallelize over a known list (`map`), race
(`race`), and delegate a single task (`copilot`). It cannot let a model decide
*how many* subtasks exist and *what* each is, then fan out and synthesize. Tasks
like "edit the N files this change requires" or "research the M relevant sources"
have no declarative home.

## Proposed Solution

```yaml
nodes:
  orchestrate:
    type: orchestrator
    plan_prompt: decompose_task     # LLM => typed list[Subtask]
    worker:
      subgraph: graphs/worker.yaml  # runs per subtask, clean context
      input_key: subtask
      output_key: result            # distilled summary (bounded tokens)
    synthesize_prompt: combine      # LLM => final result from worker summaries
    max_workers: 8                  # loop-limit / safety bound
    state_key: final
```

- **Plan** produces a Pydantic `list[Subtask]` (typed, validated — no untyped fan-out).
- **Workers** run in isolated subgraph contexts; only their summaries return.
- **Synthesize** merges summaries; raw worker context never reaches the orchestrator.
- **`max_workers`** is a hard safety bound (compounding-error / cost guard).

## Acceptance Criteria

- [ ] `orchestrator` node type with plan → fan-out → synthesize lifecycle
- [ ] Subtask list is Pydantic-typed; empty plan handled explicitly (raise, not
      silently pass)
- [ ] Workers execute in isolated contexts; only distilled summaries propagate
- [ ] `max_workers` enforced; exceeding it fails loudly
- [ ] A committed `examples/` graph demonstrating genuine runtime decomposition
      (`demo-output.log` included)
- [ ] Tests tagged with a new `REQ-YG-XXX`; capability file added
- [ ] `reference/graph-yaml.md` documents the node

## Alternatives Considered

- **`map` over an LLM-produced list**: closest existing path — an `llm` node emits
  a list, a `map` node consumes it. If this composition proves sufficient in
  practice, this FR should be **closed in favor of documenting that recipe**
  rather than adding a node. (Strong candidate; evaluate before building.)
- **`copilot` delegation**: delegates one opaque task; no typed decomposition or
  structured synthesis.

## Related

- `docs/2026-06-28-research.md` (gap #4, explicitly deferred)
- Anthropic, *Building effective agents* — orchestrator-workers; multi-agent
  research system (sub-agent architecture)
- `map`, `subgraph`, `shared-graph-invocation`, `copilot` capabilities
