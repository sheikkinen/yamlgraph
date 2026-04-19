# Diary: FR-255 Extract Shared invoke_graph

**Date:** 2026-04-19
**FR:** FR-255
**Trap:** partial_remediation — identical code in two places (mcp_server and a2a_server) that would diverge on any future fix.
**Insight:** The `_invoke_graph` pattern was copy-pasted between MCP and A2A servers verbatim. Neither consumer had any unique need — the duplication was pure cargo-culting from the first implementation to the second. Extracting to `graph_loader.py` was the minimal fix because that module already owns `load_and_compile()`.
**Cure:** callsite_fix — rather than patching each consumer, moved the shared logic to the module that owns the pipeline.

**Seed:** Could `invoke_graph` evolve to accept a `checkpointer` parameter, letting MCP/A2A servers opt into persistence without rebuilding the full CLI pipeline? If so, the CLI's `cmd_graph_run` could also delegate its compile→invoke step to this function, shrinking its surface further.
