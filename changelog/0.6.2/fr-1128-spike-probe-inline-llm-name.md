---
type: fix
scope: lint
req: REQ-YG-073
---
- **FR-1128 Spike probe inline-LLM exemption name**: The #729 spike probe is renamed to `probe_constrained_object.py` so that the existing `probe_` exemption covers it. A new unit test asserts the repository has no inline-LLM violations, so a future violation fails in CI on its own PR instead of blocking every later commit through the whole-tree hook. (REQ-YG-073)
