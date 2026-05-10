---
type: feat
scope: watcher
---
- **FR-303 Unified Watcher Pipeline**: Replaced separate integration-pipeline.yaml with action-directory-swap pattern. One canonical watcher-pipeline.yaml serves both production and integration profiles via `--actions-dir` flag. Custom action types (verify_red, changelog_gen, failure_cleanup) enable stub interception.
