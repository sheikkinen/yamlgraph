# Task brief — FR-782 self-portrait: final validation pass over both governed artifacts

Governed artifacts in scope (both, and nothing else):

- `examples/demos/self-portrait/graph.yaml`
- `examples/demos/self-portrait/prompts/synthesize_portrait.yaml`

Both already exist from earlier runs of this route. This pass validates
them against the contract below and repairs them **only** if validation
fails. If validation passes, change nothing and record that outcome.

## Contract to validate

Graph:

- `name: self-portrait`, `checkpointer: {type: memory}`,
  `prompts_relative: true`, `prompts_dir: prompts`
- Seven `type: python` tools, all
  `module: examples.demos.self-portrait.tools` (the `path:` form breaks
  the tool module's relative imports under strict tool loading)
- Nodes: `prepare`, `extract`, `enrich`, `build_payload`,
  `confirm_egress` (`type: interrupt`, `resume_key: consent_answer`),
  `verify_payload`, `synthesize` (`type: llm`, `prompt:
  synthesize_portrait`, `state_key: portrait`), `render`,
  `render_denied`
- Edges: linear `START → prepare → extract → enrich → build_payload`;
  conditional out of `build_payload` on `auto_approve`; conditional out
  of `confirm_egress` on `consent_answer == 'yes'` vs not;
  `verify_payload → synthesize → render → END`; `render_denied → END`

Prompt: inline `schema` named `SelfPortrait` with exactly the fields
`identity`, `social_graph`, `expertise`, `geography`, `rhythms`,
`evolution`, `agent_briefing`; the user template takes the single
variable `payload_json`.

The W026 lint warning about seven top-level schema fields is expected
and must NOT be "fixed" — the seven-field JSON contract is frozen by
`feature-requests/FR-782-user-self-portrait-example.md`.

## Validation to run

```bash
yamlgraph graph lint examples/demos/self-portrait/graph.yaml
yamlgraph graph validate examples/demos/self-portrait/graph.yaml
python -m pytest tests/unit/test_fr782_self_portrait.py -q --no-cov
```

All three must pass (lint may report only the expected W026 warning).

The report's `Artifacts` section must list both governed paths above.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
