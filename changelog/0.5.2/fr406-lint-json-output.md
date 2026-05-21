---
type: feat
scope: cli
req: REQ-YG-406
---
- **FR-406 Lint JSON Output**: Add `yamlgraph graph lint --json` machine mode that emits per-file `LintResult` NDJSON to stdout, keeps diagnostics on stderr, and preserves existing lint exit semantics. (REQ-YG-406)
