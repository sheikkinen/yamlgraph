---
type: fix
scope: tests
req: REQ-YG-644
---
- **FR-982 Unit suite no longer runs with the operator's LangSmith tracer live**: `yamlgraph.config` loads `.env` at import, so a developer's `LANGSMITH_TRACING=true` traced every test graph to their project and made the tracer shell out underneath positional `subprocess.run` stubs (FR-960's routing test red locally, green in CI). A session-scoped conftest fixture now overrides all four tracing aliases to `"false"` at session start (override, not delete — dotenv never overwrites), clears `langsmith.utils.get_env_var`'s lru_cache, and restores prior values at teardown; the weaker per-test `LANGCHAIN_TRACING` pop is removed. The FR-960 stub dispatches on argv (`_claude_cli`) so only `claude` calls consume scripted responses. (REQ-YG-644)
