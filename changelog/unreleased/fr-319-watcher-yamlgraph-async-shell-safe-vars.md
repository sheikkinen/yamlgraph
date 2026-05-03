---
type: feat
scope: watcher
---
- **FR-319**: Quote `YamlgraphAsyncAction` `--var` payloads with `shlex.quote()` after context substitution so inner quotes and shell metacharacters are passed literally through `create_subprocess_shell()`.
