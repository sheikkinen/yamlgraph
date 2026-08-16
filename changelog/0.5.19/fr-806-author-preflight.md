---
type: feat
scope: scripts
req: REQ-YG-598
---
- **FR-806 Author Brief Pre-Flight**: `scripts/author.sh` mechanically dry-runs the task brief before the copilot backend spawns. Paths asserted as existing inputs must exist (exit 64 quoting the violated line); validation-section command executables must statically resolve (`python -m`, env prefixes, `./relative-script`; brief text never executed); 2+ live full-pipeline smokes warn against the 900s ceiling. `--no-preflight` skips only the pre-flight — sentinel arming and the report gate remain mandatory. No LLM in the pre-flight path. (REQ-YG-598)
