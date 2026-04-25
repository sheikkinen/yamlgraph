# Forensic Failure Diary Demo

This demo showcases the **Forensic Failure Analysis** feature (FR-285) that was added to watcher2 for automated failure diagnosis and institutional learning.

## Overview

The forensic failure analysis system automatically generates diagnostic diary entries when watcher2 cycles fail, providing:
- Root cause analysis
- Evidence collection from logs and worktree state  
- Actionable recommendations for prevention
- Structured diary entries for institutional learning

## Demo Structure

- `graph.yaml` - Forensic analysis graph with ForensicAnalysis schema
- `prompts/analyze_failure.yaml` - LLM prompt for failure context analysis
- `README.md` - This documentation

## Usage

Run the demo with sample failure data:

```bash
yamlgraph graph run examples/demos/forensic-failure-diary/graph.yaml \
  --var failure_reason="implement step" \
  --var topic_content="Add new authentication module with JWT support" \
  --var log_files="tmp/watcher2-implement.log" \
  --var worktree_state="Modified: tests/test_auth.py, yamlgraph/auth.py" \
  --full
```

## Expected Output

The demo will:
1. **Analyze failure context** using the provided variables
2. **Generate structured analysis** with root cause identification
3. **Create forensic diary entry** in `docs/diary/YYYY-MM-DD-forensic.md`
4. **Return completion status**

## Integration with Watcher2

In real watcher2 usage, this analysis happens automatically in the `handle_failure()` function:
- Extracts failure context (reason, topic, logs, git state)
- Invokes `.chaplain/graphs/watcher-forensic/graph.yaml`  
- Generates forensic diary entry
- Preserves enhanced failure record in `.chaplain/failed/`

## Schema

```yaml
ForensicAnalysis:
  root_cause: str         # Primary cause of failure
  failure_reason: str     # Original failure trigger
  evidence: list[str]     # Supporting evidence
  recommendations: list[str] # Prevention measures
```

This demonstrates how YAMLGraph enables structured analysis of operational failures for continuous improvement.