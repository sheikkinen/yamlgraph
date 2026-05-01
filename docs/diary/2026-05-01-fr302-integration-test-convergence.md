## 2026-05-01: FR-302 Integration Test Convergence

### Context
End-to-end integration test for the watcher FSM pipeline. Goal: seed an inbox topic, run the full 18-state pipeline (preflight → completed), and verify clean PASS.

### Traps Encountered

**1. Pipe Interleaving (downstream_fix)**
The run script piped `statemachine ... &` background output through `| tee`. The dispatcher's continuous stdout interleaved with the foreground polling loop, preventing clean termination. The script appeared to hang because `wait` blocked on the still-writing pipe.

*Cure:* Redirect dispatcher output to a dedicated log file (`> logs/integration-dispatcher-*.log 2>&1 &`). The foreground script stays clean.

**2. Terminal State Semantic Mismatch (plausible_wrong_answer)**
The FSM engine hardcodes terminal states as `["stopped", "shutdown", "completed"]`. The pipeline config listed `failed` as terminal, but the engine never emitted `"terminal state: failed"`. The polling loop and success assertion both assumed `completed → stopped` transitions that never fire because the engine halts at `completed`.

Three distinct bugs from one root cause:
- Polling looked for `"terminal state: stopped"` — engine halts at `completed`
- Success assertion checked `"completed --job_done--> stopped"` — transition never fires
- `failed` state never logs "terminal state" — engine doesn't recognize it

*Cure:* Poll for `"terminal state: (completed|stopped)|Integration pipeline failed"`. Assert on `"terminal state: completed"`. The engine's contract is the truth, not the config's aspirational labels.

**3. State Timeout vs Action Timeout (boundary: state)**
The `waiting_ci` action had `timeout: 660` (11 min for CI), but the FSM state timeout was `timeout(300)` (5 min). The state timeout fired first, killing the pipeline mid-CI.

*Cure:* Align state timeout to `timeout(660)` to match the action timeout. The boundary is the state definition — normalize there.

**4. CI Not Triggering (boundary: platform)**
After pushing main with fixes, the next integration test's PR got no CI runs at all. The previous run's PR (same workflow, same trigger) ran CI fine. Root cause unclear — possibly GitHub Actions rate limiting or cold-start delay. Resolved by ensuring main was pushed first so the workflow definitions on the default branch were current.

### The One Law Applied
Every bug was a boundary violation: engine semantics vs config assumptions, state timeout vs action timeout, pipe ownership vs process lifecycle. Normalize at the boundary where external data enters.

### Insight
**Test count is not test coverage.** Seven runs, seven distinct bugs — each masked by the previous one's failure. The pipeline was "tested" with unit tests that all passed, but the integration surface exposed timing, pipe, and semantic contract bugs that no unit test could catch. Demo-level execution is the only proof of integration health.

### Seed
The FSM engine's hardcoded terminal state list (`["stopped", "shutdown", "completed"]`) ignores the config's `states` section. Should the engine respect config-defined terminal states? This would make `failed` properly terminal and emit the expected log line. But it changes the engine's contract — a feature request, not a bug fix.
