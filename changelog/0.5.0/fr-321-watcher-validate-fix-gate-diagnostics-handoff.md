---
type: feat
scope: watcher
---
- **FR-321**: Switch `YamlgraphAsyncAction` from shell command execution to `create_subprocess_exec(*argv)`, passing `--var` payloads as literal argv tokens and preserving existing routing/timeout behavior.
