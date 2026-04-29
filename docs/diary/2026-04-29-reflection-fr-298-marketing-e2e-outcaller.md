# Reflection: FR-298 Marketing E2E Test (Outcaller)

**Date:** 2026-04-29
**FR:** FR-298
**Duration:** ~15 minutes

## What happened

Created the automated E2E test infrastructure for the `callback_marketing`
questionnaire: answerer graph, shell wrapper, and test script. Three files
cloned from the `callback_other_topic` (NC-254) reference and adapted.

## Cognitive process

1. **Research phase** — read the context doc (`building-questionnaire-graph.md`)
   and the FR, then loaded all five reference files in a single subagent call.
   Having a comprehensive context document made the research phase trivial —
   every decision point was already documented.

2. **Key design decision** — marketing mode has no navigator, so the answerer
   graph is *simpler* than the reference (removed 4 intent-classification nodes)
   but has an *extra turn* (3 required fields across 2 answers vs 1 field in
   1 answer for other_topic).

3. **Shell wrapper composition** — the FR specified individual CLI flags
   (`--name`, `--organization`, `--memento`) rather than a raw `--answer-1`
   string. The shell script composes natural Finnish sentences from the fields,
   keeping the graph simple (just `answer_1`, `answer_2`).

## Traps avoided

- **Intent drift** — the FR explicitly stated "no navigator intent step" and
  "no graph_switch assertion." Both were correctly omitted.
- **False duplicate** — tempted to reuse the other_topic answerer's flow
  verbatim, but the marketing flow is structurally different (no intent,
  2 turns).

## Insight

**Context documents pay for themselves.** The `building-questionnaire-graph.md`
playbook made this enforcement mechanical — every file, every pattern, every
naming convention was already specified. The FR became a delta against the
playbook rather than a design-from-scratch exercise.

## Seed

Can the playbook itself generate the answerer graph? The questionnaire schema
contains field IDs and required flags — a `yamlgraph` meta-graph could read the
schema, count required fields, and emit a turn-per-gap answerer YAML automatically.
The answerer is deterministic and follows a rigid pattern; generation would
eliminate clone-and-modify drift entirely.
