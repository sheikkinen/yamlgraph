# Persona & Scenario Generator

Generate user personas and usage scenarios for a product idea, saved as interlinked markdown files.

## Pipeline

```
START → analyze_product → MAP(generate_personas) → MAP(generate_scenarios) → save_results → END
```

1. **analyze_product** (LLM) — Extracts target user segments from the product idea
2. **generate_personas** (MAP) — For each segment, generates a detailed persona
3. **generate_scenarios** (MAP) — For each persona, generates 3-5 usage scenarios
4. **save_results** (Python) — Writes interlinked markdown files to output directory

## Usage

```bash
yamlgraph graph run examples/demos/persona_scenarios/graph.yaml \
  --var product_idea="A mobile app for elderly users to manage medications" \
  --var persona_count="4" --full
```

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

~9 LLM calls for 4 personas, ~$0.30 with Anthropic.

## Files

| File | Purpose |
|------|---------|
| `graph.yaml` | Pipeline: analyze → personas → scenarios → save |
| `prompts/analyze_product.yaml` | Extract user segments (structured) |
| `prompts/generate_persona.yaml` | Generate persona (structured: name + profile) |
| `prompts/generate_scenarios.yaml` | Generate scenarios per persona (structured) |
| `nodes/save_results.py` | Write interlinked markdown files |
