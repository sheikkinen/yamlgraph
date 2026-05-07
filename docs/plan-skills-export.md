# Plan: `yamlgraph skill export`

## Concept

Export a YAMLGraph graph directory into the open Skills standard format. The output is a self-contained directory that any Skills-compatible agent (Claude Code, Cursor, Copilot, Gemini) can discover and activate.

YAMLGraph graphs already *are* Skills — procedural knowledge defined declaratively. This command provides the standardized envelope.

## Structural Mapping

| Skills Standard | YAMLGraph Equivalent |
|---|---|
| `SKILL.md` (description + instructions) | `graph.yaml` metadata + node sequence |
| `/scripts` (executable code) | `tools/` (Python tools, shell commands) |
| `/references` (domain knowledge) | `prompts/*.yaml` (Jinja2 templates with domain context) |
| `/assets` (templates, static data) | Graph `vars`, schemas, example fixtures |
| Progressive disclosure (3 tiers) | `yamlgraph graph list` → `graph info` → `graph run` |

## What Gets Generated

Given `examples/demos/hello/`:

```
output/hello-world/
├── SKILL.md              ← Generated: description, trigger, instructions
├── scripts/
│   └── run.sh            ← Generated: yamlgraph graph run invocation
├── references/
│   └── prompt-greet.md   ← Rendered from prompts/greet.yaml
└── assets/
    └── schema.json       ← JSON Schema of inputs/outputs
```

## `SKILL.md` Output (Example)

```markdown
---
name: hello-world
version: "1.0"
description: Simple greeting generator demonstrating basic LLM usage
triggers:
  - greeting generation
  - personalized welcome message
inputs:
  name: string (required) — Who to greet
  style: string (required) — Tone: formal, casual, playful
outputs:
  greeting: string — The greeting text
  emoji: string — Matching emoji
  formality_level: string — Formality label
---

# hello-world

Generate a personalized greeting with configurable style.

## When to Use

Use this skill when the user asks for a greeting, welcome message,
or personalized salutation in a specific tone or style.

## Execution

\```bash
yamlgraph graph run <graph_path> --var name="<NAME>" --var style="<STYLE>" --full
\```

## Input Schema

| Variable | Type | Description |
|----------|------|-------------|
| name | string | Who to greet |
| style | string | Tone (formal, casual, playful) |

## Output Schema

| Field | Type | Description |
|-------|------|-------------|
| greeting | string | The personalized greeting text |
| emoji | string | A single emoji matching the tone |
| formality_level | string | One-word formality label |
```

## Implementation Plan

```
Topic: Skill Export CLI Command
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. yamlgraph/cli/skill_commands.py (NEW)
   - Register `skill` subparser with `export` subcommand
   - Args: graph_dir (positional), --format (skill-md|copilot), --output-dir
   - Dispatch to export logic

2. yamlgraph/cli/__init__.py (CHANGE)
   - Import and register cmd_skill_dispatch in create_parser()

3. yamlgraph/skill_export.py (NEW)
   - export_skill(graph_path, output_dir, format) → Path
   - Reuse discovery.py to extract: name, description, input_vars, input_schema
   - Parse prompt YAML files to extract schema fields + system/user text
   - Derive "triggers" from description + prompt keywords
   - Render SKILL.md via Jinja2 template
   - Generate scripts/run.sh with correct invocation
   - Generate references/ from prompt YAML → markdown
   - Generate assets/schema.json from input_schema + output schema

4. yamlgraph/templates/skill.md.j2 (NEW)
   - Jinja2 template for SKILL.md generation
   - YAML frontmatter + markdown body

5. tests/unit/test_skill_export.py (NEW)
   - Test: hello graph produces valid SKILL.md with correct metadata
   - Test: input/output schemas extracted correctly
   - Test: multi-node graph with tools includes scripts/
   - Test: --format copilot produces .copilot/skills/ structure

6. Smoke test
   - yamlgraph skill export examples/demos/hello/ --format skill-md
   - Validate output parseable by agent (YAML frontmatter valid, paths resolve)
```

## Format Variants

| `--format` | Output | Target |
|---|---|---|
| `skill-md` | Standard open Skills directory | Any agent |
| `copilot` | `.copilot/skills/<name>/SKILL.md` | VS Code Copilot |
| `cursor` | `.cursor/skills/<name>/` | Cursor |

## Key Design Decisions

1. **Reuse `discovery.py`** — input/output separation already solved (REQ-YG-310). No new parsing logic needed.

2. **Triggers are derived, not manual** — Extract keywords from description + prompt user template. Optional `triggers:` key in graph YAML for explicit override.

3. **References are prompts rendered to markdown** — The prompt YAML is the domain knowledge. Flatten it to readable markdown so agents without YAMLGraph can still understand the procedure.

4. **`scripts/run.sh` is the execution bridge** — The Skill points to YAMLGraph as the runtime. Agents that can execute shell can run the graph. Agents that can't still get the procedural knowledge from SKILL.md.

5. **No new graph YAML schema required** — Everything needed (`name`, `description`, `state`, `nodes.*.state_key`, prompt schemas) already exists. Optional enrichment (`triggers:`, `examples:`) can come later.

## What This Unlocks

- YAMLGraph graphs become discoverable by any Skills-compatible agent without installing the framework
- The MCP server remains the "live" integration; skill export is the "portable" integration
- Graph authors get a standardized way to document their graphs for humans AND agents simultaneously
- The Skills directory can be committed to repos, making graphs available to Copilot/Cursor without MCP configuration

## Scope Boundary

**In scope:** Export command, SKILL.md generation, schema extraction, basic format variants.

**Out of scope:** Skills registry/marketplace, `yamlgraph skill install`, runtime skill loading (graphs already handle this via MCP), LLM-generated trigger descriptions (keep it mechanical).

## Context: Skills vs Tools vs RAG

| Concept | Purpose | Analogy |
|---|---|---|
| RAG | Factual Knowledge | An Encyclopedia (look up facts) |
| Tools (MCP) | Interaction | A Hammer (the ability to hit a nail) |
| Skills | Procedural Expertise | A Carpentry Apprenticeship (knowing when and how to use the hammer to build a chair) |

YAMLGraph's position: **Skills authoring framework** — the workshop where procedural knowledge is defined, tested, and executed. The `skill export` command is the packaging step that makes that knowledge portable.
