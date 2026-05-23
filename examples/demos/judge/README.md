# Judge Demo

Standalone FR judge agent that evaluates feature requests against the
YAMLGraph Scripture and produces structured verdicts.

## Usage

```bash
# Validate the graph
yamlgraph graph lint examples/demos/judge/graph.yaml

# Run the judge against a feature request
yamlgraph graph run examples/demos/judge/graph.yaml \
  --var fr_path="feature-requests/FR-448-agent-structured-output.md" --full
```

## What It Does

1. Takes `fr_path` as input (path to a feature request)
2. Reads the FR document and checks architecture references
3. Evaluates against 8 criteria from the Scripture
4. Returns a structured `JudgeVerdict` with:
   - `verdict` (APPROVE / AMEND / REJECT / SPLIT)
   - `reasoning` (explanation)
   - `criteria_results` (per-criterion pass/fail)
   - `issues` (specific items to address)

## Pipeline

```
START → judge → END
```

## Key Concepts

- **`type: agent`** — LLM agent node with tool access
- **Shell tools** — `read_fr`, `check_architecture`, `search_existing_frs`, `read_file`
- **Inline schema** — Structured output defined in prompt YAML
- **`prompts_relative: true`** — Prompts relative to graph file

## Files

```
judge/
├── graph.yaml          # Graph definition with shell tools
├── prompts/
│   └── judge.yaml      # Judge prompt with inline schema
└── demo-output.log     # Captured output from demo run
```
