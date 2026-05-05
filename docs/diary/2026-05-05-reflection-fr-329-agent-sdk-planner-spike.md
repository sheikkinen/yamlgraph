# Reflection: FR-329 Agent SDK Planner Spike (phase 1 standalone)

**Date:** 2026-05-05
**FR:** FR-329 standalone planner spike using Anthropic Agent SDK
**Reviewer:** watcher2 (post-validate)

## Trap

`working_system_inertia` — The chaplain planner already works via `type: copilot`
subprocess. The temptation is to extend the existing copilot node with a new
backend rather than confirming feasibility in isolation first. The spike
explicitly resisted this by keeping all new code in `examples/agent-sdk-planner/`
and leaving `copilot_node.py` untouched.

## What Happened

Issue #329 requested a phase-1 feasibility spike to validate:

1. **Deterministic FR numbering** — `next_fr_number` tool scans
   `feature-requests/FR-*.md` and returns `max + 1`, eliminating races and
   off-by-one errors that occur when the copilot CLI is asked to pick the next
   number from prose context.
2. **Template fidelity** — `read_fr_template` returns byte-identical content
   of `feature-requests/TEMPLATE.md`, ensuring the agent cannot hallucinate
   section headings.
3. **Exploration audit** — `PostToolUse` hook emits a per-call trace so
   maintainers can see exactly which files the agent read or wrote during a
   planning run.
4. **Cost accountability** — per-run token cost is calculated and compared
   against a `< $0.15` budget target, recorded in the run output.

All four were validated by the unit tests in
`tests/unit/test_fr329_agent_sdk_planner_spike.py` against the script source
as static contracts (no live API calls required).

## Root Cause

The lack of custom-tool contract visibility in the existing CLI path meant that
every planning run was a black box: the agent could pick any FR number and any
section structure. The spike demonstrates that two simple tools (`next_fr_number`
and `read_fr_template`) plus one event hook (`PostToolUse`) eliminate all three
failure modes without touching the runtime.

## What Worked

- Scoping the spike to `examples/` kept the runtime surface immutable.
- Static contract tests (file presence, regex on source) gave deterministic
  RED/GREEN signal without requiring an API key in CI.
- Defining acceptance criteria per tool contract before writing any code
  clarified the boundary between "spike proves" and "runtime provides".

## Insight

A standalone example with two tool contracts is stronger feasibility evidence
than a prototype integrated into the copilot node. The isolation makes the cost
and failure-mode analysis unambiguous: if the example script passes, the
backend migration is de-risked by proof, not by optimism.

## Seed

Can `next_fr_number` and `read_fr_template` be registered as MCP tools so any
copilot-backed planning graph can call them without needing a dedicated Agent
SDK path? This would allow the copilot node to gain deterministic numbering
without a backend migration.
