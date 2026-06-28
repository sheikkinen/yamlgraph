# Feature Request: Compaction Node

**Priority:** HIGH
**Type:** Feature
**Status:** Judged — Authority GRANTED with corrections (2026-06-28)
**Effort:** 2 days
**Requested:** 2026-06-28

## Summary

A first-class `compaction` node that summarizes-and-reinitializes accumulated
state (or message history) when it crosses a token threshold, so long-running
graphs stay within the model's effective attention budget instead of growing
state monotonically until quality degrades.

## Value Statement

Graph authors get long-horizon coherence for free: any multi-turn or
multi-iteration graph (chaplain pipeline, dungeon-master play loop, ebook
authoring) can run for hours without *context rot* silently eroding output
quality — without writing a line of Python.

## Value Proposal

- **Quality preservation**: Recall degrades as tokens grow (n² attention, every
  model). Compaction is the field's *first* lever against this; it converts an
  unbounded-growth failure mode into a bounded, predictable one.
- **Cost reduction**: Every token in every downstream call is paid for repeatedly.
  Compacting a 50k-token history to a 2k summary cuts per-call input cost for the
  remainder of the run — directly measurable via `--token-usage`.
- **Reuses existing strengths**: Compaction is "an LLM call that summarizes" —
  YAMLGraph already owns `execute_prompt`, Pydantic schemas, and prompt caching.
  The node is a thin, declarative wrapper, not new infrastructure.
- **Unblocks existing examples**: The dungeon-master and chaplain graphs already
  hit the window wall today; this is a felt pain, not a speculative one.

## Judgement (2026-06-28)

**Verdict: Authority GRANTED with corrections.** Strong FR — reuses owned pieces (`execute_prompt`,
Pydantic, caching), addresses felt pain (dungeon_master and chaplain hit the window wall today),
and keeps the policy declarative. The corrections below are about the one thing compaction cannot
take for granted: that the summary preserved what mattered.

**NOTE — number collision (resolved).** This FR originally shared number 616 with the linter
bug FR; that FR was renumbered to `FR-621-lint-map-subnode-tool-references.md`, and this compaction
FR keeps 616 (the research trio 616/617/618/619 cross-reference each other by number).

**Correction 1 (PRIMARY — lossy compaction needs a fidelity floor, not just a shape check).**
Compaction replaces state with a summary; the AC validates the summary's **shape** (Pydantic) but
not its **fidelity**. A summary that silently drops a load-bearing fact degrades every downstream
call — the emission-vs-fidelity trap. Bind three guards: (a) never destroy the source irrecoverably
— write the pre-compaction state to the checkpointer (or FR-617 memory) so nothing is unrecoverable;
(b) a `keep_tail` floor so the most recent items are always verbatim; (c) a smoke assertion that
named entities / still-open objectives present before compaction survive in the summary. Recall-first
prompting is necessary but not sufficient.

**Correction 2 (PRIMARY — re-trigger hysteresis).** In a loop that keeps appending over threshold,
compaction fires every iteration and re-summarizes its own previous summary — a summary of a summary
of a summary, compounding erosion of the very context it protects. Define the trigger to compact
**only new material since the last compaction**, or set a post-compaction floor + cooldown so the
summary is not immediately re-fed to itself. Without hysteresis, long loops erode fastest exactly
where compaction is supposed to help most.

**Correction 3 (secondary — conservative token estimate).** The trigger fires on an estimated token
count; a char/word heuristic is acceptable for v1 only if it **over**-estimates (fire early) rather
than under-estimates (fire late → window already blown). State the safety margin.

**Frozen scope.** Below-threshold passthrough (no LLM call, no cost); above-threshold output =
summary + `keep_tail` verbatim items; source preserved (lossy but recoverable); hysteresis against
re-compaction; demo proving a long loop stays bounded with `demo-output.log`.

## Problem

YAMLGraph has state *persistence* (checkpointing) but no notion of context as a
finite, depleting resource. The dynamic state TypedDict only grows; nothing
distills it. Long-horizon graphs therefore degrade as accumulated state crowds
the attention budget, and there is no declarative remedy — authors must drop to
custom `python` nodes and hand-roll summarization.

## Proposed Solution

A node type that, when triggered, replaces verbose state keys with an
LLM-generated high-fidelity summary, preserving a configurable tail of recent
items verbatim.

```yaml
nodes:
  compact_history:
    type: compaction
    source_key: messages          # state key to compact
    target_key: messages          # where the compacted result is written
    prompt: compaction_summary    # prompts/compaction_summary.yaml
    trigger:
      max_tokens: 40000           # compact when source exceeds this
    keep_tail: 5                  # preserve the N most-recent items verbatim
    on_skip: passthrough          # below threshold => no-op
```

- **Trigger** is evaluated against an estimated token count of `source_key`.
- **`keep_tail`** mirrors the "summary + N most-recently-accessed items" pattern.
- Summary prompt is author-supplied (recall-first, then precision — per the
  context-engineering guidance), so the policy of *what to keep* stays in YAML.
- Default summary prompt ships for the common "message history" case.

## Acceptance Criteria

- [ ] `compaction` node type registered in `node_factory/`
- [ ] Below-threshold inputs pass through unchanged (no LLM call, no cost)
- [ ] Above-threshold inputs are replaced by `summary + keep_tail` verbatim items
- [ ] Token estimate is provider-agnostic (char/word heuristic acceptable v1)
- [ ] Compacted output validated through a Pydantic schema (no untyped dict)
- [ ] A demo under `examples/demos/` proving a long loop stays bounded
      (`demo-output.log` included)
- [ ] Tests tagged with a new `REQ-YG-XXX`; capability file added
- [ ] `reference/graph-yaml.md` documents the node

## Alternatives Considered

- **Tool-result clearing only** (lightest form): cheaper but coarser; revisit as
  a follow-up flag (`clear_tool_results: true`) on this same node.
- **Larger context windows**: rejected — context pollution and relevance concerns
  persist regardless of window size; bigger windows defer rather than solve.
- **Custom `python` node per graph**: the status quo; duplicates summarization
  logic and hides the policy from the declarative layer.

## Related

- `docs/2026-06-28-research.md` (gap #1)
- Anthropic, *Effective context engineering for AI agents* (Sep 2025) — compaction
- `yamlgraph/executor.py`, `yamlgraph/node_factory/`
