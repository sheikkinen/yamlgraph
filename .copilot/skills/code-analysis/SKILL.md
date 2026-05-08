---
name: code-analysis
description: 'Run comprehensive code quality analysis on a Python package. Use when: auditing code quality, checking for linting issues, dead code, security vulnerabilities, test coverage, or complexity hotspots. Runs ruff, pytest, bandit, radon, vulture, and reports prioritized recommendations.'
argument-hint: 'Package path like "yamlgraph" or "src/myapp"'
---

# Code Analysis

Run a full suite of static analysis and testing tools against a Python codebase, then generate prioritized improvement recommendations.

## When to Use

- User asks for code quality audit or analysis
- Evaluating a package before refactoring
- Checking for security issues, dead code, or complexity
- Pre-release quality gate check
- Answering "what should I fix next?"

## Execution

This skill delegates to a YAMLGraph pipeline that runs 8 shell tools and synthesizes results.

```bash
yamlgraph graph run examples/demos/code-analysis/graph.yaml --var package="<PACKAGE>" --var path="<PATH>" --full
```

### Inputs

| Variable | Type | Description |
|----------|------|-------------|
| `path` | string | Directory path to analyze (e.g., `yamlgraph`, `src/app`) |
| `package` | string | Python package name for coverage (e.g., `yamlgraph`) |

### Tools Run

1. **ruff** — Linting and style checks
2. **pytest** — Test suite execution
3. **coverage** — Line coverage report
4. **bandit** — Security vulnerability scan
5. **radon** — Cyclomatic complexity analysis
6. **vulture** — Dead/unused code detection
7. **line count** — Largest files by LOC
8. **TODOs** — Unresolved TODO/FIXME/HACK markers

### Outputs

| Field | Description |
|-------|-------------|
| `analysis_results` | Raw output from all 8 tools |
| `recommendations` | Prioritized, actionable improvement list |

## Fallback (Manual)

If `yamlgraph` is not available, run the tools individually:

```bash
ruff check <path> --output-format=concise
python -m pytest tests/ -q --tb=no --cov=<package> --cov-report=term | tail -30
bandit -r <path> -ll -q
radon cc <path> -a -s --min C
vulture <path> --min-confidence 80
grep -rn "TODO\|FIXME" <path> --include="*.py" | head -20
```

Then synthesize findings into a prioritized recommendation list.
