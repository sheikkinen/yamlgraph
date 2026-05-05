# Agent SDK Planner Spike (FR-329)

Standalone feasibility spike that converts a topic file into a feature request
markdown file using the Anthropic Agent SDK.

## What it validates

1. Deterministic FR numbering via `next_fr_number` (`max + 1` over `FR-*.md`)
2. Template fidelity via `read_fr_template` (`feature-requests/TEMPLATE.md`)
3. Post-tool exploration audit traces via `PostToolUse` hook output
4. Per-run cost reporting with a `< $0.15` target budget

## Prerequisites

```bash
pip install claude-agent-sdk
export ANTHROPIC_API_KEY="your-key"
```

## Usage

```bash
python examples/agent-sdk-planner/plan.py .chaplain/processing/gh-329.md
```

Optional flags:

```bash
python examples/agent-sdk-planner/plan.py .chaplain/processing/gh-329.md \
  --model claude-sonnet-4-5 \
  --max-budget-usd 0.15
```

Output path contract:

```text
feature-requests/FR-XXX-<slug>.md
```
