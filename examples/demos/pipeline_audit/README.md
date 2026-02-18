# Pipeline Audit

Cross-pipeline structural analysis: quality gates, silent fallbacks, `on_error:skip` without reporting, shared pattern detection.

## Usage

**From the graph directory** (required for tool imports):

```bash
cd examples/demos/pipeline-audit

# Audit entire project
yamlgraph graph run graph.yaml --var scan_dir="../../.."

# Audit a specific example
yamlgraph graph run graph.yaml --var scan_dir="../../../examples/book_translator"

# Focus on a specific concern
yamlgraph graph run graph.yaml --var scan_dir="../../.." --var focus="quality_gates"
```

**Direct Python usage** (no LLM required):

```python
from tools.audit_tools import scan_graphs_tool, count_patterns_tool, scan_python_nodes_tool

# Get inventory of all graphs
print(scan_graphs_tool(scan_dir="/path/to/yamlgraph"))

# Get pattern counts
print(count_patterns_tool(scan_dir="/path/to/yamlgraph"))

# Scan Python nodes for anti-patterns
print(scan_python_nodes_tool(scan_dir="/path/to/yamlgraph"))
```

## What It Scans

### Graph Structure (`scan_graphs_tool`)
- Node types (llm, map, agent, interrupt, etc.)
- `on_error` settings (skip, retry, fallback, fail)
- Quality gate detection by name/prompt keywords
- Loop detection in edges

### Python Anti-patterns (`scan_python_nodes_tool`)
- Bare `except:` (silent fallbacks)
- `or []` / `or {}` fallbacks
- Inline `model_dump` without `to_serializable`
- Manual `.get('result')` patterns

### Pattern Counts (`count_patterns_tool`)
```
total_graphs: 80
total_nodes: 257
type: llm: 130
type: map: 17
on_error: skip: 6
quality_gate_nodes: 6
```

## Findings Guide

| Finding | Risk | Action |
|---------|------|--------|
| `on_error:skip` without SkipReport | Hidden failures | Add `SkipReport` to collect skipped items |
| Map node without quality gate | Unvalidated bulk output | Add evaluation node after map |
| No quality gates | Missing validation | Consider adding review/grade nodes |
| Bare `except:` | Silent errors | Add specific exception handling |

## Related

- [reference/contrib.md](../../../reference/contrib.md) — `SkipReport` for skip visibility
- [FR-043](../../../feature-requests/043-evaluation-framework.md) — Evaluation framework proposal
- [FR-044](../../../feature-requests/044-shared-contrib-libraries.md) — Contrib library design
