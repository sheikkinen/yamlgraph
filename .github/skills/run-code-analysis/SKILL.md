---
name: run-code-analysis
description: "Run code quality analysis on YAMLGraph. Use when: running ruff, bandit, radon, vulture, pytest coverage, checking code quality, finding dead code, security scanning, or generating improvement recommendations. For autonomous analysis, use the code-analysis agent instead."
argument-hint: "target path like 'yamlgraph' or specific tool like 'ruff'"
---

# Run Code Analysis

Run automated code quality tools and generate recommendations. Canonical source: `reference/code-analysis.md`.

**Note:** The `code-analysis` agent can run this autonomously. This skill covers manual usage.

## Quick Start (Graph-Based)

```bash
yamlgraph graph run examples/demos/code-analysis/graph.yaml \
  --var path="yamlgraph" \
  --var package="yamlgraph"
```

## Individual Tools

### Ruff (Linting + Style)

```bash
ruff check yamlgraph/                    # Check
ruff check --fix yamlgraph/              # Auto-fix
ruff format yamlgraph/                   # Format
```

### Pytest (Tests + Coverage)

```bash
# Fast parallel (skip slow)
pytest tests/unit/ -q --no-cov -m "not slow" -n auto

# With coverage
pytest tests/ --cov=yamlgraph --cov-report=html
```

### Bandit (Security)

```bash
bandit -r yamlgraph/ -ll -q
```

Flags: `-ll` = medium+ severity, `-q` = quiet (issues only).

### Radon (Complexity)

```bash
radon cc yamlgraph/ -a -nc              # Cyclomatic complexity
radon mi yamlgraph/                     # Maintainability index
```

Target: functions < complexity 10. Module size: < 400 lines, max 450.

### Vulture (Dead Code)

```bash
vulture yamlgraph/ vulture_whitelist.py
```

The whitelist file suppresses intentional unused exports.

### Additional Checks

```bash
# Find TODOs/FIXMEs
grep -rn "TODO\|FIXME" yamlgraph/

# Line counts
find yamlgraph/ -name "*.py" | xargs wc -l | sort -n | tail -20

# Import boundary check
lint-imports
```

## Code Quality Standards

| Metric | Target |
|--------|--------|
| Module size | < 400 lines (max 450) |
| Function complexity | < 10 (radon cc) |
| Test coverage | ≥ 80% |
| Security issues | 0 medium+ (bandit) |
| Dead code | 0 unreported (vulture) |

## Graph Structure

The code-analysis graph uses an agent node with shell tools:

```yaml
nodes:
  run_analysis:
    type: agent
    prompt: code-analysis/analyzer
    tools: [run_ruff, run_tests, run_bandit, run_radon, run_vulture]
    max_iterations: 12
    state_key: analysis_results

  generate_recommendations:
    type: llm
    prompt: code-analysis/recommend
    requires: [analysis_results]
    state_key: recommendations
```

## Prerequisites

```bash
pip install ruff bandit radon vulture
```
