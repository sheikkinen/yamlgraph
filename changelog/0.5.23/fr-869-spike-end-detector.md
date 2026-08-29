---
type: feat
scope: hooks
req: REQ-YG-527
---
- **FR-869 Spike-End Detector**: the PreToolUse command guard now warns (stderr, never blocking) when a plain `git commit` runs in a foreign repo with no `pre-commit` hook — and escalates the warning when the staged diff adds `schedule:` or `secrets.` lines to `.github/workflows/*`, i.e. the commit takes an unenforced repo live. A repo-root `.ramp-declined` marker suppresses both with an audited reason; every warning writes a stable non-secret audit entry (`ramp-unenforced`, `ramp-spike-end`, `ramp-declined`). (REQ-YG-527)
