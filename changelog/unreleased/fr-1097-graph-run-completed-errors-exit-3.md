---
type: fix
scope: cli
req: REQ-YG-700
---
- **FR-1097 `graph run` exits 3 when a completed run recorded untolerated errors**: a non-stream run that finished but appended untolerated `state.errors` entries exited 0. It now writes all output and exports, prints `⚠ completed with N errors (M tolerated)` to stderr and exits 3. Skip and warn errors are tolerated (`PipelineError.tolerated`); imported and checkpoint-retained errors never count; malformed error entries exit 1. `--json` and the `run_end` route-log event carry both counts. `build_skip_error_state` now returns only its delta, and exported state serializes errors as objects instead of `repr` strings. The five adapter wrappers name rc 3 and keep their artifact verdicts. (REQ-YG-700)
