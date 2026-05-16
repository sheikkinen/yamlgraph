# Prompt Theme Analyzer Demo

FR-402 demo showing the architecture-aligned pattern:

`list (python) -> map(llm) -> aggregate (python) -> group (llm) -> write (python)`

## What this demonstrates

1. High-volume `map` fan-out over prompt files
2. Boundary normalization in Python (`source_dir` required, prompt truncation)
3. Deterministic aggregation before second-stage LLM grouping
4. Markdown report writing in a Python side-effect node

## Pipeline

1. `list_prompts`: scans `<source_dir>/*/prompts.txt`, filters invalid/refusal payloads, truncates text to 2000 chars
2. `classify_themes`: map node classifying each prompt into a concise theme
3. `aggregate_themes`: deterministic Python count of normalized themes
4. `group_themes`: LLM grouping over `theme_counts` (aggregated input only)
5. `write_report`: outputs markdown report to `output_path`

## Usage

```bash
yamlgraph graph lint examples/demos/prompt_theme_analyzer/graph.yaml

yamlgraph graph run examples/demos/prompt_theme_analyzer/graph.yaml \
  --var source_dir="/path/to/prompt-runs" \
  --var output_path="outputs/prompt-theme-report.md" \
  --full
```

## Integration evidence

AC-07 is integration-scoped (live LLM call). This change set satisfies it via
the committed `demo-output.log`.

## Files

| File | Purpose |
|------|---------|
| `graph.yaml` | 5-node graph with deterministic aggregation |
| `prompts/classify_theme.yaml` | Per-item theme classifier prompt |
| `prompts/group_themes.yaml` | Grouping prompt over aggregated counts |
| `tools.py` | `list_prompts`, `aggregate_themes`, `write_report` |
| `analyze.sh` | Fast local non-LLM prompt corpus summary |
| `demo-output.log` | Proof log for successful end-to-end run |
