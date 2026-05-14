# Feature Request: FR-382 Prompt caching for Chaplain system prompts

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-05-14

## Summary

Convert all Chaplain pipeline prompt `system:` blocks to `system_segments:` with
`cache: true` on the static preamble sections. Zero Python code change. Pure YAML
configuration. Reduces repeated input token cost by 80–90% across plan→judge→enforce
pipeline cycles.

## Value Statement

The Chaplain plan→judge→enforce→validate→sanity cycle invoking 5 nodes in rapid
succession currently re-sends identical Scripture and instruction preambles on every
call at full input token price. Prompt caching eliminates that cost for all repeat
invocations within the 5-minute cache TTL.

## Problem

15 Chaplain prompt YAML files use bare `system:` blocks. Every invocation sends the
full system prompt as fresh input tokens. For a single plan→judge→enforce cycle:

- `plan-unified.yaml`: ~200 tokens system (repeated 1×/cycle)
- `judge.yaml`: ~150 tokens system
- `enforce-session.yaml`: ~300 tokens system (Scripture excerpt)
- `validate-session.yaml`: ~200 tokens system
- `sanity-check-session.yaml`: ~200 tokens system

Across a typical FR enforcement run (5 nodes, 3–5 invocations each) the static
system prompt corpus is sent 15–25 times. At Sonnet 4.6: $3/MTok input.

With prompt caching: cache write is $3.75/MTok (first call), cache read is
$0.30/MTok (all subsequent). On 20 repeat reads: **90% reduction on cached tokens**.

## Background

YAMLGraph already supports `system_segments` with caching (FR-219, CAP-131).
The syntax is available, tested, and documented. This FR is a configuration
change, not a feature addition.

Anthropic's documentation recommends using 1-hour cache duration (`cache_ttl: 3600`)
for batch workloads. The Chaplain runs sequentially, so 5-minute TTL is sufficient
unless the Chaplain FSM is extended to batch mode (see FR-381 Seed).

## Proposed Solution

For each of the 15 Chaplain prompt files, convert `system:` to `system_segments:`
splitting the prompt into:

1. **Static preamble** (role + Scripture + working rules): `cache: true`
2. **Dynamic variables** (worktree_dir, branch, fr_path): not cached

### Example transformation

**Before** (`enforce-session.yaml`):
```yaml
system: |
  You are implementing a feature in the YAMLGraph framework.
  You have full tool access: terminal, file editing, and code search.

  Your objective: make the acceptance tests pass and commit the result.
  ...
  The Scripture commands:
  - Commandment 7: Red-Green-Refactor...
  ...
  Working directory: {{ worktree_dir }}
  Branch: {{ branch }}
  Feature request: {{ fr_path }}
```

**After**:
```yaml
system_segments:
  - text: |
      You are implementing a feature in the YAMLGraph framework.
      You have full tool access: terminal, file editing, and code search.

      Your objective: make the acceptance tests pass and commit the result.
      ...
      The Scripture commands:
      - Commandment 7: Red-Green-Refactor...
      ...
    cache: true
  - text: |
      Working directory: {{ worktree_dir }}
      Branch: {{ branch }}
      Feature request: {{ fr_path }}
```

### Files to update

All 15 Chaplain prompt files that currently use bare `system:`:

| File | Static tokens (est.) |
|------|----------------------|
| `.chaplain/graphs/watcher-plan/prompts/plan-unified.yaml` | ~200 |
| `.chaplain/graphs/watcher-plan/prompts/judge.yaml` | ~150 |
| `.chaplain/graphs/watcher-plan/prompts/plan.yaml` | ~180 |
| `.chaplain/graphs/watcher-plan/prompts/research.yaml` | ~120 |
| `.chaplain/graphs/watcher-plan/prompts/summarize.yaml` | ~80 |
| `.chaplain/graphs/watcher-plan/prompts/write-acceptance-tests.yaml` | ~120 |
| `.chaplain/graphs/watcher-enforce/prompts/enforce-session.yaml` | ~300 |
| `.chaplain/graphs/watcher-enforce/prompts/validate-session.yaml` | ~200 |
| `.chaplain/graphs/watcher-enforce/prompts/sanity-check-session.yaml` | ~200 |
| `.chaplain/graphs/watcher-enforce/prompts/context-planner.yaml` | ~100 |
| `.chaplain/graphs/watcher-diary/prompts/reflect.yaml` | ~150 |
| `.chaplain/graphs/watcher-forensic/prompts/analyze_failure.yaml` | ~120 |
| `.chaplain/graphs/philosopher/prompts/challenge.yaml` | ~100 |
| `.chaplain/graphs/philosopher/prompts/analyze.yaml` | ~100 |
| `.chaplain/graphs/philosopher/prompts/distill.yaml` | ~100 |
| `.chaplain/graphs/philosopher/prompts/reflect.yaml` | ~100 |

## Acceptance Criteria

- [ ] AC-01: All Chaplain prompt files use `system_segments:` with at least one
  `cache: true` segment containing the static role/instruction preamble
- [ ] AC-02: Dynamic Jinja2 variables (`{{ worktree_dir }}` etc.) remain in
  uncached segments only — no cached segment contains runtime-variable text
- [ ] AC-03: `yamlgraph graph lint` passes on all modified prompt files
- [ ] AC-04: Existing Chaplain integration tests pass unchanged
- [ ] AC-05: `prompt_caching_demo` smoke test continues to pass
- [ ] Changelog fragment in `changelog/unreleased/`
- [ ] Diary reflection in `docs/diary/`

## Constraints

1. No Python code changes. YAML files only.
2. Minimum cacheable segment size: Anthropic requires ≥1024 tokens for caching.
   If a static segment is shorter, it will not be cached (API silently ignores);
   no error, just no savings. Verify each prompt's static block is substantive.
3. Copilot CLI backend (`type: copilot`) does not use `system_segments` — it
   constructs its own system prompt from the `system:` field. Only `type: llm`
   nodes benefit. Verify each node type before converting.
4. Sequencing: this FR is Priority 1 per `docs/plan-token-cost-mitigation.md`.
   Should land before FR-381 (Batch API).

## Alternatives Considered

### No change
Accept full input cost on every invocation. Valid if Chaplain runs are infrequent.
Rejected: with 100+ FRs processed per month, savings are material.

### Include ARCHITECTURE.md / Scripture in cached segments
High-value: the full Scripture (~3000 tokens) is repeated in every enforce prompt
via the Copilot system instructions. However, those live in `.github/copilot-instructions.md`
and are injected by the Copilot CLI, not by YAMLGraph — not accessible for
`system_segments` caching via the Anthropic API directly.

## Related

- FR-219: Anthropic Prompt Caching demo (`system_segments` syntax)
- FR-381: Batch API — prompt caching can be combined inside batch requests
- `docs/plan-token-cost-mitigation.md` — Priority 1 in the mitigation plan
- `examples/demos/prompt-caching/` — working reference implementation
