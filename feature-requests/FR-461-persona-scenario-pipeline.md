# Feature Request: Persona & Scenario Generation Pipeline

**Priority:** MEDIUM
**Type:** Feature
**Status:** Completed
**Effort:** 2 days
**Requested:** 2026-05-27

## Summary

A YAMLGraph demo pipeline that generates user personas and usage scenarios for a given product idea. Output is a folder of interlinked markdown files — one per persona, one per scenario — cross-referenced so teams can navigate personas↔scenarios naturally. Useful for research, development planning, and test case generation.

## Value Statement

Product teams get a browsable folder of interlinked persona and scenario documents from a single CLI invocation, demonstrating YAMLGraph's map nodes and Python tool output patterns.

## Problem

Creating realistic user personas and usage scenarios is a manual, time-consuming process. Teams often skip it or produce shallow archetypes. When they do create personas, the link between persona and concrete usage scenarios is implicit — scattered across documents or lost entirely. YAMLGraph lacks a demo showing research/analysis pipelines with file-based output.

## Proposed Solution

### Pipeline Architecture

The logic is a straightforward chain — no cartesian products:

```
START
  │
  ▼
analyze_product (LLM)
  │  Extracts: target_segments list
  │
  ▼
generate_personas (MAP over segments)
  │  For each segment → rich persona markdown
  │
  ▼
generate_scenarios (MAP over personas)
  │  For each persona → 3-5 usage scenarios specific to that persona
  │
  ▼
save_results (Python tool)
  │  Writes interlinked markdown files to outputs/ folder
  │
  ▼
END
```

**Key insight:** Scenarios belong to a persona, not to a capability×persona cross. Each persona's goals, frustrations, and context naturally generate the scenarios relevant to them.

### Directory Structure

```
examples/demos/persona_scenarios/
├── graph.yaml              # Full pipeline: product → personas → scenarios → save
├── README.md
├── nodes/
│   ├── __init__.py
│   └── save_results.py     # Write interlinked markdown files
└── prompts/
    ├── analyze_product.yaml
    ├── generate_persona.yaml
    └── generate_scenarios.yaml
```

### Output Structure

```
outputs/persona_scenarios/{timestamp}/
├── index.md                # Product summary + links to all personas
├── persona-01-anna.md      # Persona detail + links to her scenarios
├── persona-02-mikko.md
├── scenario-01-01-morning-meds.md    # Links back to persona-01
├── scenario-01-02-refill-alert.md
├── scenario-02-01-setup-help.md
└── ...
```

Every file is interlinked:
- `index.md` links to each `persona-NN-*.md`
- Each persona file links back to `index.md` and forward to its `scenario-NN-*.md` files
- Each scenario file links back to its parent persona

### Graph YAML (graph.yaml)

```yaml
name: persona-scenario-pipeline
version: "1.0"
description: "Generate personas and scenarios for a product idea, save as interlinked markdown"
prompts_relative: true
prompts_dir: prompts

tools:
  save_results:
    type: python
    module: examples.demos.persona_scenarios.nodes.save_results
    function: save_results
    description: "Write interlinked persona and scenario markdown files"

nodes:
  analyze_product:
    type: llm
    prompt: analyze_product
    state_key: product_analysis
    variables:
      product_idea: "{state.product_idea}"
      persona_count: "{state.persona_count}"

  generate_personas:
    type: map
    over: "{state.product_analysis.target_segments}"
    as: segment
    node:
      prompt: generate_persona
      state_key: persona
      variables:
        product_idea: "{state.product_idea}"
        segment: "{state.segment}"
    collect: personas

  generate_scenarios:
    type: map
    over: "{state.personas}"
    as: persona
    node:
      prompt: generate_scenarios
      state_key: scenarios
      variables:
        product_idea: "{state.product_idea}"
        persona: "{state.persona}"
    collect: all_scenarios

  save:
    type: python
    tool: save_results
    state_key: output_dir

edges:
  - from: START
    to: analyze_product
  - from: analyze_product
    to: generate_personas
  - from: generate_personas
    to: generate_scenarios
  - from: generate_scenarios
    to: save
  - from: save
    to: END
```

### Prompts

**analyze_product.yaml** — Structured output:
- `target_segments: list[str]` — 3-6 user segments (e.g. "elderly users living alone", "caregivers", "pharmacists")
- `product_summary: str` — one-paragraph product description for use in downstream prompts

**generate_persona.yaml** — Unstructured markdown. For each segment, produce a rich persona document:
- Name, age, location, role
- Goals (what they want from the product)
- Frustrations (current pain points)
- Context (tech comfort, daily routine, environment)
- Key quote (one sentence capturing their mindset)

Markdown output — rich narrative matters more than structured fields.

**generate_scenarios.yaml** — Given a persona, produce 3-5 usage scenarios specific to that persona's goals and frustrations. Each scenario:
- Title (short, descriptive)
- User story: As [persona], I want [action] so that [outcome]
- Steps: happy path (numbered)
- Edge cases: 2-3 things that could go wrong for this specific persona
- Emotional context: how the persona feels during this interaction

The persona's frustrations and context drive the scenarios — a tech-savvy caregiver gets different scenarios than an elderly user living alone.

### Python Tool (save_results.py)

Follows the `save_prompts.py` pattern from Image Pipeline — timestamped output directory:

```python
from pathlib import Path
from datetime import datetime
import re

OUTPUT_BASE = Path("outputs/persona_scenarios")

def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]

def save_results(state: dict) -> dict:
    personas = state.get("personas", [])
    all_scenarios = state.get("all_scenarios", [])
    product = state.get("product_analysis", {})
    summary = (
        product.product_summary if hasattr(product, "product_summary")
        else product.get("product_summary", "")
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = OUTPUT_BASE / timestamp
    out.mkdir(parents=True, exist_ok=True)

    persona_files = []
    # Write persona files
    for i, persona in enumerate(personas, 1):
        slug = _slugify(str(persona)[:40])
        fname = f"persona-{i:02d}-{slug}.md"
        persona_files.append((i, fname, persona))

    # Build index.md
    index_lines = [f"# Personas & Scenarios\n\n{summary}\n\n## Personas\n"]
    for i, fname, _ in persona_files:
        index_lines.append(f"- [{fname}]({fname})")
    (out / "index.md").write_text("\n".join(index_lines) + "\n")

    # Write each persona + its scenarios
    for i, fname, persona in persona_files:
        persona_text = str(persona)
        scenario_block = all_scenarios[i - 1] if i - 1 < len(all_scenarios) else ""
        scenarios_text = str(scenario_block)

        # Parse individual scenarios from the block, write separate files
        scenario_files = _write_scenario_files(out, i, scenarios_text)

        # Persona file with links
        links = "\n".join(f"- [{sf}]({sf})" for sf in scenario_files)
        content = f"[← index](index.md)\n\n{persona_text}\n\n## Scenarios\n\n{links}\n"
        (out / fname).write_text(content)

        # Each scenario file links back
        for sf in scenario_files:
            path = out / sf
            old = path.read_text()
            path.write_text(f"[← {fname}]({fname}) · [← index](index.md)\n\n{old}")

    return {"output_dir": str(out)}
```

### CLI Usage

```bash
# Generate personas + scenarios, save as interlinked markdown
yamlgraph graph run examples/demos/persona_scenarios/graph.yaml \
  --var product_idea="A mobile app for elderly users to manage medications" \
  --var persona_count="4" --full

# Output: outputs/persona_scenarios/{timestamp}/
# Open index.md and navigate via links
```

**Cost estimate:** 4 personas × (1 persona prompt + 1 scenario prompt) + 1 analysis = ~9 LLM calls, ~$0.30 with Anthropic.

## Patterns Borrowed

| Pattern | Source | Usage Here |
|---------|--------|------------|
| Structured analysis → map expansion | Innovation Matrix `pipeline.yaml` | analyze → map personas → map scenarios |
| Python tool for file output | Image Pipeline `save_prompts.py` | `save_results.py` writes interlinked markdown |
| Structured + unstructured mix | Innovation Matrix prompts | Structured analysis, rich persona/scenario text |
| Timestamped output directory | Image Pipeline | `outputs/persona_scenarios/{timestamp}/` |

## Acceptance Criteria

- [ ] `yamlgraph graph lint examples/demos/persona_scenarios/graph.yaml` passes
- [ ] Pipeline runs: `--var product_idea="..." --var persona_count="4"`
- [ ] Output folder contains `index.md`, `persona-*.md`, `scenario-*.md`
- [ ] `index.md` links to all persona files
- [ ] Each persona file links back to `index.md` and forward to its scenario files
- [ ] Each scenario file links back to its parent persona
- [ ] Scenarios are driven by persona goals/frustrations (not generic)
- [ ] README.md with usage examples
- [ ] Demo output log (`demo-output.log`) proving execution
- [ ] Changelog fragment in `changelog/unreleased/`
- [ ] Diary entry in `docs/diary/`

## Alternatives Considered

1. **Single monolithic prompt** — Rejected: loses the structured decomposition that makes results useful. A single "generate everything" prompt produces shallow personas.
2. **Cartesian product (persona × capability)** — Rejected (was in v1 of this FR): produces combinatorial explosion and scenarios disconnected from persona context. Scenarios should flow from persona goals, not from crossing abstract dimensions.
3. **Test case generation stage** — Deferred: adds a third map pass and doubles LLM cost. Scenarios with edge cases already provide test-like structure. Can be added as a follow-up pipeline stage.
4. **JSON output instead of markdown** — Rejected: markdown is human-browsable, interlinked, and can be committed to a repo or opened in any editor. JSON requires tooling to navigate.

## Related

- `examples/demos/innovation_matrix/` — Structural inspiration (dimensions → map → synthesize)
- `examples/image_pipeline/` — File output pattern (`save_prompts.py`)
- `examples/demos/feature-brainstorm/` — Adjacent ideation demo
- `reference/graph-yaml.md` — Map node, tool, and edge configuration

---

## Judgement

**Verdict: Approved with required amendments.**

### Issue 1: Unstructured map output shape (BLOCKING)

Map nodes wrapping unstructured text produce `{"_map_index": N, "value": "text"}` dicts, not plain strings. The FR assumes `personas` and `all_scenarios` are `list[str]` — they're `list[dict]`.

This breaks:
- `{state.persona}` in the second map's prompt variables — passes a dict, not persona text
- `save_results.py` treating personas as strings
- `_slugify(str(persona)[:40])` slugifying a dict repr

**Fix:** Use structured schemas for both persona and scenario prompts. Interlinked file output *requires* structure (at minimum `name`/`title` for filenames + `content` for body). "Rich unstructured markdown" and "interlinked files with meaningful names" are contradictory goals. Resolve by using schemas:

```yaml
# analyze_product.yaml schema
schema:
  name: ProductAnalysis
  fields:
    target_segments: {type: "list[str]", description: "3-6 user segments"}
    product_summary: {type: str, description: "One-paragraph product description"}

# generate_persona.yaml schema
schema:
  name: Persona
  fields:
    name: {type: str, description: "Persona name (e.g. Anna Virtanen)"}
    segment: {type: str, description: "User segment this persona represents"}
    profile: {type: str, description: "Full persona profile in markdown"}

# generate_scenarios.yaml schema
schema:
  name: ScenarioSet
  fields:
    persona_name: {type: str, description: "Name of the persona these scenarios belong to"}
    scenarios: {type: "list[str]", description: "3-5 scenario documents, each in markdown"}
```

With structured output, map collect produces `list[dict]` with known fields. The `save_results.py` tool can safely access `.name`, `.profile`, `.scenarios` etc.

### Issue 2: Missing `_write_scenario_files` (BLOCKING)

The `save_results.py` code calls `_write_scenario_files(out, i, scenarios_text)` but never defines it. With the structured schema fix above, this function becomes straightforward — iterate over the `scenarios` list field instead of parsing markdown by headers.

### Issue 3: Persona↔scenario alignment (MINOR)

The FR assumes `all_scenarios[i - 1]` gives scenarios for persona `i`. This holds because `sorted_add` preserves `_map_index` ordering. But using structured output with `persona_name` in the scenario schema provides an explicit link rather than relying on positional alignment.

### Issue 4: `persona_count` variable unused in graph (MINOR)

The `analyze_product` prompt receives `persona_count` to control segment count, but there's no guarantee the LLM returns exactly that many. The prompt should instruct "exactly N segments" and the schema should validate. Alternatively, drop `persona_count` and let the LLM decide segment count naturally (simpler, equally useful).

### Revised acceptance criteria amendment

Add:
- [ ] Persona and scenario prompts use inline schemas (not unstructured)
- [ ] `save_results.py` includes complete `_write_scenario_files` implementation
- [ ] Scenario files include persona name in back-link text (not just filename)

### Scope freeze

- 4 nodes: analyze → map personas → map scenarios → save
- 3 prompts, all with inline schemas
- 1 Python tool (`save_results.py`)
- Single `graph.yaml` (no pipeline.yaml / graph.yaml split)
- No test case generation stage (deferred)
- No synthesize node (the files are the output)

Approved for enforcement.
