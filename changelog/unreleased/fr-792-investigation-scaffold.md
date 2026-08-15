---
type: feat
scope: scripts
req: REQ-YG-596
---
- **FR-792 Multi-Step Investigation Scaffold**: `python scripts/scaffold_investigation.py --name <slug> --steps <csv> --home <path> [--stub]` generates a lintable N-step investigation skeleton from the pattern proven by the API discovery family — tool_call orchestrator with TODO skip-condition edges, per-step graph-runtime manifests, agent graph stubs with typed `findings`/`confidence` schemas, prompt stubs, and a governance-aware `tools/README.md`. `--stub` emits deterministic passthrough steps so the orchestrator runs end-to-end without provider keys (pytest smoke asserts final state shape). Script surface only — no CLI subcommand, no runtime changes; committing generated governed artifacts still requires the graph-authoring route. (REQ-YG-596)
