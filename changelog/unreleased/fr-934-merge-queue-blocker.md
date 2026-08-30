---
type: fix
scope: ci
---
- **FR-934 Merge queue blocked by platform**: The `merge_queue` ruleset rule is only available on organization-owned repositories; the API rejects it (422) on this user-owned repo after validating every parameter. The merged `merge_group` wiring stays dormant and correct; the strict up-to-date regime remains. CLAUDE.md and doc pins corrected to the enforced truth; blocker and probe evidence recorded in FR-934.
