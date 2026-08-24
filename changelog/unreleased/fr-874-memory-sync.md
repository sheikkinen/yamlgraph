---
type: feat
scope: scripts
req: REQ-YG-620
---
- **FR-874 Cross-Device Agent Memory Sync**: `scripts/memory_sync.py` mirrors the machine-local memory-tool scopes through the git-tracked `docs/agent-memory/` store (repo-scope notes + explicitly promoted user notes only). Import applies a manifest base-hash conflict contract (never mtime), sanitizes note paths, and supports read-only subrepo discovery via `YAMLGRAPH_AGENT_MEMORY_ROOT`. SessionStart hook imports fail-open with bounded JSONL audit evidence. (REQ-YG-620)
