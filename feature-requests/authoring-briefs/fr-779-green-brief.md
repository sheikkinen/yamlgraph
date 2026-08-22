# Task: FR-779 GREEN — research-agent bindings and grounded-synthesis gate

Governing FR: feature-requests/FR-779-research-agent-demo-rot.md (judged
APPROVED WITH REVISIONS; conditions C-1..C-6). RED suite committed:
tests/unit/test_fr779_research_agent_demo.py (7 failing tests define the
target shape exactly).

## Single file to modify

examples/demos/research-agent/graph.yaml — nothing else. No prompt
changes, no tool changes, no yamlgraph/ changes.

## Change 1: variable bindings (AC-02)

Replace whole-string bare placeholders with state paths:

- `extract_intent.variables.query`: `"{query}"` → `"{state.query}"`
- `plan_research.variables.scope`: `"{scope}"` → `"{state.scope}"`
- `execute_research.variables.scope`: `"{scope}"` → `"{state.scope}"`
- `synthesize_report.variables.query`: `"{query}"` → `"{state.query}"`

Add top-level state declarations (lint E007 otherwise):

```yaml
state:
  query: str
  scope: str
```

Leave `{state.intent}`, `{state.plan}`, `{state.findings}`,
`{state.validation}` bindings untouched.

## Change 2: synthesis gate (AC-04/AC-05, judgement R-2 terminal contract)

Replace the unconditional edge `validate_findings → synthesize_report`
with two conditional edges:

```yaml
  - from: validate_findings
    to: END
    condition: "validation.confidence == 'low' or findings == ''"
  - from: validate_findings
    to: synthesize_report
    condition: "validation.confidence != 'low' and findings != ''"
```

Keep `synthesize_report → END` as is. Empty findings / low confidence
terminates after validate_findings with the validation verdict preserved
in state and no report produced.

## Validation

- `yamlgraph graph lint examples/demos/research-agent/graph.yaml`
- `yamlgraph graph validate examples/demos/research-agent/graph.yaml`
- `pytest tests/unit/test_fr779_research_agent_demo.py -q --no-cov` — all 8 must pass.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
