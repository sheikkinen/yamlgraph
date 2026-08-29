---
type: fix
scope: vscode
---
- **FR-898 ledger --tap on store-less machines**: `iter_requests()` no longer crashes when the VS Code workspaceStorage directory is absent (Linux CI); absent store dir yields an empty report.
