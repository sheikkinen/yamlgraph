# Authoring brief: FR-1125 questionnaire — `classify` moves off Anthropic

Governing FR: feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md
(ledger `docs/issues-2026-09-27-fr1125-census.md`, row for
`examples/questionnaire/prompts/classify_recap.yaml` path `corrections`;
disposition option 2, the judgement's recommended default, chosen by the
operator: the object's keys are field ids and are genuinely unknown
ahead of time, so declaring properties would invent them, which
judgement C-7 forbids).

Repository boundary: **this repository**, target file
`examples/questionnaire/graph.yaml`. The prompt
`examples/questionnaire/prompts/classify_recap.yaml` is **not** edited:
its `corrections: dict[str, str]` stays exactly as committed, and the
Python consumer `apply_corrections` keeps reading a mapping.

## Task

Modify **exactly one file**: `examples/questionnaire/graph.yaml`. In
the `classify` node (the node whose `prompt` is `classify_recap`), add
one line: `provider: mistral`. Nothing else changes: `defaults.provider:
anthropic` stays for every other node; no edge, tool, state or
`config:` entry changes. Add a one-line YAML comment above the new line:
`# FR-1125: corrections is an open object (field id -> value); Anthropic constrained decoding cannot express it.`

Mistral is the repository's second most used static provider (14
declarations on `main`) and accepts open objects under its structured
output; no other provider choice is authorised by this brief.

## Validation

- Before the edit, record the complete output of
  `yamlgraph graph lint examples/questionnaire/graph.yaml`; after the
  edit, the identical command. The after set must contain no E016,
  E017, W028 or W029.
- `yamlgraph graph validate examples/questionnaire/graph.yaml`
- `python -m pytest tests/unit -k "questionnaire or fr1125" -q --no-cov`
- No live smoke by brief (the questionnaire is an interactive demo).
  Record "no smoke, by brief".

**Prior art:** FR-1125 (governing FR; judgement R-1 option 2 and C-7);
`reference/prompt-yaml.md` § Nested Objects ("an object declared
without `properties` is an unconstrained object … use it when the keys
are genuinely unknown ahead of time").
