---
type: fix
scope: race
req: REQ-YG-266
---
- **FR-705 Race Timeout Candidate Fidelity**: a race-node timeout now raises `AllCandidatesFailedError` at the point where candidate context exists — already-failed candidates keep their real exceptions and every still-pending candidate is enumerated by `provider/model` name with `race timed out after Xs`. Previously the error collapsed to `All 1 race candidates failed: - ?/?: race timed out` regardless of fleet size (NC-361: forensics had to pull LangSmith child runs to learn which providers were pending). The synthetic `[({}, exc)]` wraps in both `race_node` and `router_race_node` are deleted; the `on_error: skip` contract keeps its `TIMEOUT_ERROR` classification whenever deadline expiry ended the race. (REQ-YG-266)
