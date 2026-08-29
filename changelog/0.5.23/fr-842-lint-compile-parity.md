---
type: fix
scope: linter
req: REQ-YG-605
---
- **FR-842 Lint/Compile Validation Parity**: `yamlgraph graph lint` now runs the loader's `validate_config` before its style/semantic checks and reports each rejection as an `E000` error carrying the unchanged validator message — lint can no longer approve a graph the loader refuses (live witness: GitClaw intake run 32361594593 failed at compile on a parenthesized edge condition that lint had passed). Existing checks still run alongside a compile-validation error so it never hides unrelated findings; JSON output and exit-code semantics are unchanged; the condition grammar is unchanged (grouping stays rejected — use flat per-branch edges, documented in the CLI reference). (REQ-YG-605)
