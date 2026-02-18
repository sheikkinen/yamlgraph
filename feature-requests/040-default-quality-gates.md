# Feature Request: Default Quality Gates for Map Nodes

**Priority:** MEDIUM
**Type:** Feature
**Status:** DEFERRED
**Effort:** 3 days
**Requested:** 2026-02-17

## Judgment (2026-02-17)

**Verdict:** DEFER — Revisit after FR-044 (contrib libraries).

**Reasoning:** Real problem, but coupling `review:` config directly to map nodes adds framework complexity. Users can already wire review nodes manually using existing primitives. The map node API is stable; adding optional config increases surface area without proven demand.

**Dependency:** FR-044 (contrib.quality) provides the building blocks. Once `collect_failures()` and review aggregation patterns are extracted and proven, integrating `review:` into map config becomes lower risk.

**Alternative for now:** Document the pattern (generate → review map → retry map) as a recipe in `reference/patterns.md`. Let users wire it explicitly. If 3+ projects adopt the pattern, automate.

## Summary

Every map node should automatically pair with a review map that evaluates, judges, and regenerates failed items. Quality gates should be the default pipeline behavior, not an opt-in exception.

## Problem

Only 2 of 10 YAMLGraph pipelines have quality gates (novel generator's grade-based loop, book translator's score-based review). The other 8 pipelines generate and save with no quality check. The lesson generator's 81 lessons go straight to disk. The innovators toolkit trusts the LLM unconditionally.

This was historically justified by cost: if every lesson needs a reviewer LLM call, that doubles API cost. But flash-tier models now cost ~$0.001/call — reviewing 81 lessons costs $0.08. The cost objection has evaporated. The real objection was latency, but with async parallelism, 81 reviews take the same wall-clock time as 1.

The novel generator already proves the pattern works: generate → analyze → evolve ↺. It should be the standard, not the exception.

## Proposed Solution

Add a `review` option to map nodes in graph YAML that enables automatic quality gating:

```yaml
nodes:
  generate_lessons:
    type: map
    state_key: lessons
    items_key: topics
    node_ref: generate_single_lesson
    review:
      enabled: true
      prompt: review_lesson          # LLM-as-judge prompt
      threshold: 0.7                 # minimum acceptable score
      max_retries: 2                 # regenerate failed items up to N times
      report_key: quality_report     # state key for quality summary
```

Behavior:
1. Map generates all items in parallel (existing behavior)
2. Review map evaluates each item against the review prompt
3. Items scoring below threshold are regenerated (up to `max_retries`)
4. A quality report is written to state: `{passed: 18, failed: 2, retried: 2, final_failures: 0}`
5. Items that fail after all retries are flagged, not silently accepted

The review prompt uses a standard schema:

```yaml
# prompts/review_lesson.yaml
schema:
  name: ReviewResult
  fields:
    score: {type: float, description: "Quality score 0.0-1.0"}
    passed: {type: bool, description: "Meets quality threshold"}
    issues: {type: list[str], description: "Specific issues found"}
    suggestions: {type: list[str], description: "Improvement suggestions"}
```

## Acceptance Criteria

- [ ] Map nodes accept optional `review` configuration
- [ ] Review runs automatically after map generation completes
- [ ] Failed items are regenerated up to `max_retries` times
- [ ] Quality report is written to state with pass/fail/retry counts
- [ ] Items that fail all retries are flagged with errors, not silently accepted
- [ ] `review.enabled: false` or omitting `review` preserves current behavior
- [ ] Tests added with `@pytest.mark.req` tags
- [ ] Documentation updated in `reference/graph-yaml.md`

## Alternatives Considered

- **Manual review nodes:** Current approach — users wire up their own review loops. Works but error-prone and not reused across pipelines.
- **Post-pipeline batch review:** Review all items after the pipeline completes. Loses the ability to regenerate inline.
- **Quality threshold at graph level:** Single threshold for all maps. Less flexible than per-node configuration.

## Related

- Novel generator's grade-based loop (`projects/novel-generator/graphs/novel.yaml`)
- Book translator's score-based review (`examples/book_translator/`)
- Diary entry: "The Constraint Shift" — Observation 1
- Kertomus `validate` node (informational only, doesn't gate)
