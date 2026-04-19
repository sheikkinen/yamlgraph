---
type: feat
scope: pipeline
req: REQ-YG-259
---
- **FR-256 Pipeline Timing Metrics**: Instrument `enforce_worktree.sh`, `bugfix_worktree.sh`, and `watch.sh` with timing/outcome JSON emission to `tmp/pipeline-metrics/`. Add `pipeline_summary.py` read-only aggregation script for daily summaries. (REQ-YG-259)
