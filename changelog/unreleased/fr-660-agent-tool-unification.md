---
type: feat
scope: agent
---
- **FR-660 Unify agent tool bind/execute paths**: Eliminated dual-path dispatch in `agent.py` where the bind path created `StructuredTool` wrappers but the execute path bypassed them with `isinstance` dispatch. Now `tool_lookup` stores `StructuredTool` instances and execution uses a single `.invoke()` call for all tool types (shell, python, graph). Removed 38 lines and the `callable(x) and not hasattr(x, 'invoke')` heuristic. (REQ-YG-018)
