# Authoring brief: FR-1121 daily_digest example — ranker schema and error policy

Governing FR: feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.md
(judgement D-3; this brief closes the YAMLGraph-repository authoring run).

Repository boundary: **this repository** (`sheikkinen/yamlgraph`), target
directory `examples/daily_digest/`. The standalone digest repository has
its own brief (`fr-1121-digest-ranker-brief.md`) and is not touched by
this run.

## Task

Modify **exactly two files**:

1. `examples/daily_digest/prompts/rank_stories.yaml` — in `schema.fields.stories`,
   change `type: list[Any]` to `type: list[dict]`. The description, the
   system and user templates, and every other field stay byte-identical.
2. `examples/daily_digest/graph.yaml` — in the `rank_stories` node, add
   `on_error: fail` (one line). No other node, edge, `defaults`, `tools`
   or `state` entry changes.

Nothing else: no node additions or removals, no prompt wording changes,
no `state:` changes. `analyze_all` keeps its sub-node `on_error: skip`
exactly as committed.

Related artifacts edited by the FR's enforcement, not by this run, named
so the report can list them: the unit witness under `tests/unit/` that
builds the ranker model from the prompt file and passes its JSON schema
through the Anthropic SDK transform (REQ-YG-664), and one changelog
fragment under `changelog/unreleased/`.

## Validation

- Before the edit, record the complete output of
  `yamlgraph graph lint examples/daily_digest/graph.yaml` in the report;
  after the edit, run the identical command and record it again. The
  after set must be unchanged or reduced, and no diagnostic may point
  at `rank_stories` or its prompt schema (judgement R-3).
- `yamlgraph graph validate examples/daily_digest/graph.yaml`
- `python -m pytest tests/unit -k fr1121 -q --no-cov` — the transform
  witness must pass after the edit.
- No live smoke: the example's full pipeline is a paid provider run and
  is not authorised by this brief. Record "no smoke, by brief" in the
  report's validation section.

**Prior art:** FR-1121 (governing FR; this brief executes its D-3
surface); FR-905 (the `RankedStory` Python boundary that the retyped
schema relies on — unchanged); FR-998 (the binder change that made the
old schema fail); FR-1073 H-2 row 10 (the sibling authoring precedent
for this same graph's map node, already applied).
