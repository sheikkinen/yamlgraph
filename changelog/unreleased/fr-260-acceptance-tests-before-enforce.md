---
type: feat
scope: chaplain
req: REQ-YG-263
---
- **FR-260 Acceptance Tests Before Enforce**: Move worktree creation into the plan-judge loop and add a `write_acceptance_tests` step between research and judge. Judge now evaluates three artifacts: FR, research brief, and failing tests. Enforce receives pre-committed RED tests as a contract. (REQ-YG-263)
