# Extended Thinking Demo (FR-071)

Demonstrates Anthropic's extended thinking feature with configurable reasoning depth.

## What is Extended Thinking?

Claude 3.7+ models support **extended thinking** - allocating extra tokens for internal reasoning before generating the final response. This trades latency and cost for deeper, more careful reasoning.

## Quick Start

```bash
# Run with default thinking budget (8000 tokens)
yamlgraph graph run examples/demos/thinking/graph.yaml \
  --var question="Explain why the sky is blue using wave theory and atmospheric physics" \
  --full

# Run with minimal thinking budget
yamlgraph graph run examples/demos/thinking/graph.yaml \
  --var question="What is 2+2?" \
  --full

# Compare: disable thinking on the quick node
yamlgraph graph run examples/demos/thinking/graph.yaml \
  --var question="List three prime numbers" \
  --full
```

## How It Works

```yaml
defaults:
  provider: anthropic
  model: claude-3-7-sonnet-20250219  # Thinking requires 3.7+
  thinking_budget: 8000               # Allocate 8000 tokens for reasoning
  temperature: 1                      # Auto-set to 1 (required)

nodes:
  deep_analysis:
    prompt: analyze
    state_key: analysis
    # Inherits thinking_budget: 8000

  quick_response:
    prompt: respond
    state_key: response
    thinking_budget: 0  # Override: disable thinking for this node
```

## Budget Guidelines

- **None/0**: Thinking disabled (normal response)
- **1024-4096**: Light reasoning (quick clarifications)
- **4096-8192**: Moderate reasoning (analysis, planning)
- **8192+**: Deep reasoning (complex problems, research)

> ⚠️ **Cost Impact**: Thinking tokens count toward usage. 8000 tokens ≈ 6 pages of text for reasoning.

## Temperature Override

When `thinking_budget ≥ 1024`, Anthropic **requires `temperature=1`**. YAMLGraph:
1. Automatically overrides temperature to 1
2. Logs a warning if you set a different temperature
3. Uses the overridden value for LLM caching

```yaml
# This works but logs a warning:
defaults:
  temperature: 0.7      # Will be overridden to 1.0
  thinking_budget: 8000

# Prefer explicit temperature=1:
defaults:
  temperature: 1        # No warning
  thinking_budget: 8000
```

## Linter Checks

The graph linter warns about common mistakes:

```bash
yamlgraph graph lint examples/demos/thinking/graph.yaml
```

Warnings:
- **W071-1**: `temperature != 1` with `thinking_budget > 0`
- **W071-2**: Non-Anthropic provider with `thinking_budget > 0`
- **W071-3**: Pre-3.7 model with `thinking_budget > 0`
- **W071-4**: `0 < thinking_budget < 1024` (below minimum)

## Architecture

```
┌─────────────────────────────────────┐
│  User Question                      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  deep_analysis (thinking: 8000)     │
│  - Spends up to 8000 tokens         │
│  - Reasoning before response        │
│  - Temperature forced to 1.0        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  quick_response (thinking: 0)       │
│  - No extended reasoning            │
│  - Fast, direct response            │
│  - Uses normal temperature          │
└──────────────┬──────────────────────┘
               │
               ▼
        Final Answer
```

## When to Use Thinking

**Good for:**
- Complex reasoning (math, logic, analysis)
- Multi-step planning
- Code architecture decisions
- Research synthesis
- Careful fact-checking

**Not needed for:**
- Simple questions
- Creative writing
- Casual conversation
- Pre-formatted responses

## See Also

- FR-071: Feature Request
- REQ-YG-083: Requirement
- `reference/graph-yaml.md`: Full YAML reference
