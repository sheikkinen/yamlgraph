---
type: fix
scope: watcher
---
- **Fix watcher2 plan step**: Write FR directly to `feature-requests/` instead of gitignored `.chaplain/drafts/`. Removes `drafts_dir` indirection from prompts, step graphs, and orchestrator.
