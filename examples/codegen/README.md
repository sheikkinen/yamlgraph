# Codegen Example - Implementation Agent

A self-contained example demonstrating YAMLGraph for code analysis and implementation planning.

## Overview

The **impl-agent** analyzes user stories/feature requests and produces actionable implementation guidance with file:line references. It uses a 5-node LLM pipeline with 24 Python analysis tools.

## Quick Start

```bash
# From project root
yamlgraph graph run examples/codegen/impl-agent.yaml -f \
  -v 'story=Add a timeout parameter to the websearch tool' \
  -v 'scope=yamlgraph/tools'
```

## Architecture

```
Parse Story → Plan Discovery → Execute Discovery → Synthesize → Generate Plan
     ↓              ↓                 ↓                ↓             ↓
   story      discovery_plan    discovery_findings  code_analysis  instructions
```

### Nodes

| Node | Type | Purpose |
|------|------|---------|
| `parse_story` | LLM | Extract key concepts from user story |
| `plan_discovery` | LLM | Create tool execution plan |
| `execute_discovery` | Map/Tool | Execute planned tool calls in parallel |
| `synthesize` | LLM | Combine findings into code analysis |
| `generate_plan` | LLM | Create implementation instructions |

### Tools (24 total)

**Code Navigation:**
- `list_modules` - List all modules in a package with summaries
- `get_structure` - Get classes, functions, imports with line numbers
- `read_lines` - Read specific line ranges from files
- `search_file` - Search for patterns in a file (grep)
- `search_code` - Search across files (grep -r)

**Semantic Analysis (jedi-based):**
- `find_refs` - Find all references to a symbol
- `get_callers` - Get functions that call a target
- `get_callees` - Get functions called by a target
- `get_signature` - Get function signature with types

**Git Context:**
- `git_blame` - Get blame info for a line
- `git_log` - Get recent commits for a file

**Meta Analysis:**
- `summarize_module` - Compress module to key abstractions
- `find_similar` - Find similar code patterns
- `find_tests` - Find related test functions

## Example Output

```
## Implementation Guide: Add timeout to websearch

### Target Files
1. yamlgraph/tools/websearch.py (lines 45-120)
   - Key function: search_web()
   - Add timeout parameter with default 30s

### Instructions
MODIFY search_web (lines 45-67) in websearch.py
  Add timeout: int = 30 parameter
  Pass to httpx.get(url, timeout=timeout)

ADD validation (after line 50) in websearch.py
  if timeout <= 0: raise ValueError("timeout must be positive")
```

## Running Tests

```bash
# Run codegen example tests only
pytest examples/codegen/tests/ -v

# Run with coverage
pytest examples/codegen/tests/ --cov=examples.codegen
```

## File Structure

```
examples/codegen/
├── impl-agent.yaml          # Graph definition
├── prompts/                 # LLM prompt templates
│   ├── parse_story.yaml
│   ├── plan_discovery.yaml
│   ├── discover.yaml
│   ├── analyze.yaml
│   ├── synthesize.yaml
│   └── generate_plan.yaml
├── tools/                   # Python analysis tools
│   ├── ai_helpers.py        # Summarize, find similar
│   ├── ast_analysis.py      # Module structure
│   ├── code_context.py      # Read lines, search
│   ├── code_nav.py          # Package navigation
│   ├── dependency_tools.py  # Import analysis
│   ├── example_tools.py     # Find examples, tests
│   ├── git_tools.py         # Git blame, log
│   ├── impl_executor.py     # Generate shell scripts
│   ├── jedi_analysis.py     # Semantic analysis
│   ├── meta_tools.py        # Graph introspection
│   ├── syntax_tools.py      # Syntax validation
│   └── template_tools.py    # Test scaffolding
├── models/
│   └── schemas.py           # Pydantic output schemas
└── tests/                   # 195 tests
```

## Extending

To add new tools:

1. Add function to appropriate module in `tools/`
2. Register in `impl-agent.yaml` under `tools:`
3. Update `plan_discovery.yaml` to include in Available Tools

To modify output format:

1. Edit `generate_plan.yaml` prompt and schema
2. Update `impl_executor.py` if parsing changes
