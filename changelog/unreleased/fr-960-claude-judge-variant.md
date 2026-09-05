---
type: feat
scope: judge
req: REQ-YG-642
---
- **FR-960 Claude judge variant**: the sole-route judge graph gains an opt-in `judge_claude` node (`backend: claude`, FR-959) beside the default Copilot node, selected by `JUDGE_BACKEND=claude scripts/judge.sh <fr>` through a state-conditioned edge — two backends, one graph, one prompt, one wrapper. The Claude judge has exactly four tools available and approved (`Read, Glob, Grep, Write`) and no bypass. `scripts/judge.sh` now writes `tmp/draft-judgement-<backend>-<fr-slug>.md` instead of one fixed name, so two backends on one FR or two FRs back to back no longer delete each other's drafts; unknown backends exit 64 before the lock. (REQ-YG-642)
