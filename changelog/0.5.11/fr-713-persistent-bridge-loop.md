---
type: feat
scope: race
req: REQ-YG-541
---
- **FR-713 Persistent Bridge Loop (Part A)**: the sync→async bridge is promoted from a per-invocation daemon-thread + `asyncio.run()` to ONE long-lived event loop thread (`yamlgraph-bridge-loop`) in `yamlgraph/utils/bridge.py`. Per-call thread churn and fresh-loop SDK reconnects are eliminated (local instrument: anthropic Δp50 +0.527 s → +0.073 s); the FR-707 shutdown-blocker and FR-712 loop-affinity defect classes become unreachable by construction. Post-verdict drain is scoped per invocation; budget-breach abandonment cancels the submitted work; the loop starts lazily, resets across fork, and restarts with a WARNING after loop-thread death. Client construction moved off-loop to the caller thread. (REQ-YG-269)
