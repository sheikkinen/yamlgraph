---
type: feat
scope: release
req: REQ-YG-188
---
- **FR-192 Draconian Changelog Release Gate**: Three-layer enforcement preventing changelog release drift — pre-commit hook blocks version bump with orphaned fragments, atomic `scripts/release.sh` enforces correct freeze→bump→commit→tag ordering, CI `release-hygiene` job validates tag-to-changelog alignment on tag push. (REQ-YG-188, REQ-YG-189, REQ-YG-190)
