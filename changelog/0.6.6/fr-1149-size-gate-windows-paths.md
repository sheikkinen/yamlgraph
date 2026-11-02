---
type: fix
scope: hooks
req: REQ-YG-631
---
- **FR-1149 The hooks key their files by POSIX paths on Windows**: `scripts/size_gate.py`, `scripts/noqa_coverage.py` and `scripts/hedging_check.py` now compare a file by its forward-slash path on every OS (`baseline_key`, `rel_key`, `_finding_key`), so on Windows the held oversize files, the documented noqa and the allowlisted findings are recognised instead of failing every commit. `yamlgraph/utils/llm_providers.py` is held at 473 lines by one temporary size-gate entry until FR-1148's split removes it; six drifted `docs/confessions.md` line references are realigned. Output on macOS and Linux is unchanged. (REQ-YG-631)
