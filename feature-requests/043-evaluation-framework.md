# Feature Request: Pipeline Evaluation Framework

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
**Effort:** 5 days
**Requested:** 2026-02-17

## Summary

Add a structured evaluation framework to YAMLGraph: generate → evaluate against rubric → iterate → log quality scores → compare against baseline. Track pipeline output quality as a measurable metric over time.

## Problem

All 10 YAMLGraph pipelines generate. None evaluate well.

- The kertomus pipeline has `validate` but doesn't act on failures — it's informational only.
- The novel generator loops on grades but the threshold is arbitrary and not tracked over time.
- No pipeline has a measurable quality metric that persists between runs.
- No pipeline compares output quality against a baseline or previous run.

The infrastructure for observability exists (LangSmith tracing), but quality evaluation is not systematized. A pipeline that ran yesterday and produced 81 lessons cannot tell you whether today's run on a different subject is better or worse. There's no quality regression detection.

With generation now near-free, **evaluation is the bottleneck.** The hard problem isn't producing content — it's knowing whether the content is good. This is the quality-speed frontier: you can generate infinitely, but you can only ship what you can verify.

## Proposed Solution

### Evaluation in Graph YAML

```yaml
metadata:
  evaluation:
    rubric: evaluate_lesson_rubric     # prompt defining quality criteria
    baseline: baselines/psykologia.json # previous run scores for comparison
    log: evaluations/                   # directory for evaluation logs
    threshold: 0.75                     # minimum acceptable mean score

nodes:
  generate_lessons:
    type: map
    state_key: lessons
    items_key: topics
    node_ref: generate_single_lesson

  evaluate_lessons:
    type: map
    state_key: evaluations
    items_key: lessons
    node_ref: evaluate_single_lesson
    # Built-in evaluation node type
    evaluation:
      dimensions:
        - accuracy
        - completeness
        - pedagogical_quality
        - engagement
      scoring: 1-5
      aggregate: mean
```

### Evaluation Rubric Prompt

```yaml
# prompts/evaluate_lesson_rubric.yaml
system: |
  You are a curriculum quality evaluator. Score each dimension 1-5.
template: |
  Evaluate this lesson plan:
  {{ lesson | tojson }}

  Score each dimension:
  - accuracy: Factual correctness (1=major errors, 5=flawless)
  - completeness: Covers required topic depth (1=superficial, 5=comprehensive)
  - pedagogical_quality: Sound teaching methodology (1=poor, 5=excellent)
  - engagement: Student interest and interaction (1=boring, 5=compelling)

schema:
  name: LessonEvaluation
  fields:
    accuracy: {type: int, description: "1-5 score"}
    completeness: {type: int, description: "1-5 score"}
    pedagogical_quality: {type: int, description: "1-5 score"}
    engagement: {type: int, description: "1-5 score"}
    overall: {type: float, description: "Weighted mean score"}
    issues: {type: list[str], description: "Specific issues found"}
```

### CLI Integration

```bash
# Run with evaluation
yamlgraph graph run graphs/generate.yaml --evaluate

# Compare against baseline
yamlgraph eval compare evaluations/run-2026-02-17.json baselines/psykologia.json

# Set baseline from current run
yamlgraph eval baseline evaluations/run-2026-02-17.json --output baselines/psykologia.json

# View evaluation summary
yamlgraph eval summary evaluations/run-2026-02-17.json
```

### Evaluation Log Format

```json
{
  "run_id": "2026-02-17T14:30:00",
  "graph": "graphs/generate.yaml",
  "variables": {"subject": "psykologia", "module": "PS3"},
  "items_total": 18,
  "items_passed": 16,
  "items_failed": 2,
  "mean_score": 3.8,
  "dimension_scores": {
    "accuracy": 4.1,
    "completeness": 3.6,
    "pedagogical_quality": 3.9,
    "engagement": 3.5
  },
  "baseline_comparison": {
    "delta": +0.2,
    "regression": false
  }
}
```

## Acceptance Criteria

- [ ] Evaluation rubric defined as a YAML prompt with structured schema
- [ ] `--evaluate` flag triggers evaluation after generation
- [ ] Evaluation scores logged to JSON files per run
- [ ] `yamlgraph eval compare` compares two evaluation runs
- [ ] `yamlgraph eval baseline` sets a baseline from a run
- [ ] Quality regression detected when scores drop below baseline - threshold
- [ ] LangSmith traces include evaluation scores as metadata
- [ ] Works with any map-based pipeline (not lesson-specific)
- [ ] Tests added with `@pytest.mark.req` tags
- [ ] Documentation with examples for common evaluation patterns

## Alternatives Considered

- **LangSmith evaluators:** Use LangSmith's built-in evaluation framework. Tight coupling to one observability vendor; YAMLGraph should be vendor-neutral for evaluation.
- **External evaluation tools:** Integrate with RAGAS, DeepEval, or similar. Adds dependencies and doesn't leverage YAMLGraph's existing prompt/schema system.
- **Manual spot-checking:** Current approach — human reads samples. Doesn't scale and isn't tracked over time.

## Related

- Novel generator quality loop (`projects/novel-generator/graphs/novel.yaml`)
- Kertomus validate node (informational only)
- LangSmith integration (`CLAUDE.md` environment variables)
- Diary entry: "The Constraint Shift" — Observation 4
- FR-040 (quality gates) — complementary; FR-040 gates individual items, FR-043 tracks pipeline-level quality
