---
type: feat
scope: copilot
req: REQ-YG-087
---
- **FR-081 Copilot Node Type** (CAP-30, REQ-YG-087, REQ-YG-089): New `copilot` node for delegating to GitHub Copilot CLI
  - `type: copilot` — invokes Copilot CLI with `--silent` flag and configurable `cli_flags`
  - `backend: cli` — subprocess execution with list-based command (injection-safe)
  - `cli_flags`: `allow_all_paths`, `allow_all_tools`, `model` options
  - `timeout` field (default 300s) per-node configurable
  - `CopilotResult` model: `output`, `exit_code`, `model`, `backend`
  - `examples/copilot/`: Plan → Judge → Summarize demo based on `.chaplain/watch.sh`
  - `reference/graph-yaml.md`: Full `type: copilot` documentation section
  - 12 tests covering all three requirements
