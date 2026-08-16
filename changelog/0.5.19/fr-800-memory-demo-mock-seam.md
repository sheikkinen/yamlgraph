---
type: fix
scope: tests
req: REQ-YG-025
---
- **FR-800 Memory-Demo Mock Seam Correction**: retarget the shell-tool mock in `test_tool_results_stored_in_state` to the FR-660 seam (`yamlgraph.tools.tool_builders.execute_shell_tool`) and assert the mock call, restoring the `_tool_results` witness broken since 085f3aad. (REQ-YG-025)
