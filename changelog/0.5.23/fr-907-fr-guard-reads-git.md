---
type: fix
scope: process
req: REQ-YG-627
---
- **FR-907 FR-number guard reads git, not the filesystem**: the uniqueness guard globbed `feature-requests/`, so a parallel session's *uncommitted* FR failed the suite on `main` for a file that was never in `main`. It now enumerates via `git ls-files`, with a test that plants an untracked probe and asserts it is invisible. (REQ-YG-627)
