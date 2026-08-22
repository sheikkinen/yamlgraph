# Authoring Brief: five-whys prompt fix — literal {problem} placeholder leak

**Governing context:** Rite of Correction (Inspect → Amend). Defect
witnessed by the FR-853 demo-gate run; condemning RED test committed:
`tests/unit/test_five_whys_prompt_rendering.py`.

**Prior art:** fr-853-task-shapes-brief.md — same FR arc, description-only
metadata edits; this brief fixes a distinct prompt-rendering defect that
FR-853's demo-gate exposed. Disposition: sibling brief, no overlap.

## Defect

`format_prompt` (yamlgraph/executor_base.py) auto-detects Jinja2 when a
template contains `{%` or `{{`. Both five-whys prompt templates mix
Jinja2 blocks with bare simple placeholders, which Jinja2 renders
LITERALLY — the model receives `Problem: {problem}` and answers
"Problem statement not provided."

## Task

Fix the two prompt files so all placeholders use Jinja2 syntax. Change
placeholder syntax only — do not reword prose, restructure schemas, or
touch any other file.

1. `examples/demos/five-whys/prompts/ask_why.yaml` — in the `user`
   template, replace `{problem}` with `{{ problem }}`. Audit the rest of
   the template (and `system`) for any other bare `{var}` placeholders
   and convert them the same way.

2. `examples/demos/five-whys/prompts/summarise.yaml` — same conversion
   for every bare placeholder (at minimum `{problem}`; audit for others,
   e.g. `{analysis}`).

## Validation

- `pytest tests/unit/test_five_whys_prompt_rendering.py -q --no-cov`
  must pass (currently RED).
- `yamlgraph graph lint examples/demos/five-whys/graph.yaml` must pass.
- Full-run smoke:
  `yamlgraph graph run examples/demos/five-whys/graph.yaml --var problem="The nightly backup job silently stopped running last week" --full`
  — the resulting summary must reference the backup job, not a missing
  problem statement. Record honestly in the report.
