# Persona & Scenario Generator

Generate user personas and usage scenarios for any product idea — output is a set of interlinked markdown files you can browse, edit, or feed into downstream tools.

Built with [YAMLGraph](https://github.com/sami-heikkinen/yamlgraph) — a framework that lets you define LLM pipelines entirely in YAML. No Python glue code for orchestration; just declare nodes, prompts, and edges.

## Quick Start

### 1. Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install yamlgraph
```

### 2. Configure

```bash
cp .env.sample .env
# Edit .env — add your LLM provider API key
```

### 3. Run

```bash
yamlgraph graph run graph.yaml \
  --var product_idea="A mobile app for elderly users to manage medications" \
  --full
```

That's it. Output lands in `outputs/persona_scenarios/<timestamp>/`.

## What YAMLGraph Does

YAMLGraph turns YAML files into executable LLM pipelines via [LangGraph](https://langchain-ai.github.io/langgraph/). This demo uses three core concepts:

| Concept | File | What it does |
|---------|------|-------------|
| **Graph** | `graph.yaml` | Declares nodes, edges, state, and tools — the pipeline topology |
| **Prompts** | `prompts/*.yaml` | Prompt templates with Jinja2 support and inline output schemas |
| **Tools** | `nodes/save_results.py` | Python functions the graph can call as side effects |

The graph compiler reads these YAML files and produces a runnable LangGraph `StateGraph` — no boilerplate, no manual wiring.

## Pipeline

```
START → analyze_product → MAP(generate_personas) → MAP(generate_scenarios) → save_results → END
```

1. **analyze_product** (LLM) — Extracts target user segments from the product idea
2. **generate_personas** (MAP) — For each segment, generates a detailed persona with name, profile, goals
3. **generate_scenarios** (MAP) — For each persona, generates 3-5 usage scenarios driven by their context
4. **save_results** (Python) — Writes interlinked markdown files to output directory

### Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `product_idea` | Product description | Required |
| `persona_count` | Number of user segments to generate | `"4"` |

## Output

```
outputs/persona_scenarios/{timestamp}/
├── index.md                           # Product summary + links to all personas
├── persona-01-anna-virtanen.md        # Persona + links to her scenarios
├── persona-02-mikko-lahtinen.md
├── scenario-01-01-morning-meds.md     # Links back to persona-01
├── scenario-01-02-refill-alert.md
├── scenario-02-01-setup-help.md
└── ...
```

All files are interlinked:
- `index.md` → links to each persona
- Each persona → links back to index, forward to its scenarios
- Each scenario → links back to its parent persona

## Cost

~9 LLM calls for 4 personas, ~$0.30 with Anthropic Claude.

## Files

| File | Purpose |
|------|---------|
| `graph.yaml` | Pipeline: analyze → personas → scenarios → save |
| `prompts/analyze_product.yaml` | Extract user segments (structured) |
| `prompts/generate_persona.yaml` | Generate persona (structured: name + profile) |
| `prompts/generate_scenarios.yaml` | Generate scenarios per persona (structured) |
| `nodes/save_results.py` | Write interlinked markdown files |
| `.env.sample` | Template for API key configuration |

## Learn More

- [YAMLGraph Documentation](https://github.com/sami-heikkinen/yamlgraph)
- [Graph YAML Reference](https://github.com/sami-heikkinen/yamlgraph/blob/main/reference/graph-yaml.md)
- [Prompt YAML Reference](https://github.com/sami-heikkinen/yamlgraph/blob/main/reference/prompt-yaml.md)
