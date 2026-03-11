---
type: feat
scope: enforce
---
- **FR-125 Enforce Pipeline Post-Merge Finalization**: Add a `finalize_merge.sh` script that runs after a PR from the enforce pipeline is merged, automating three post-merge obligations: CHANGELOG entry, FR status update, and diary reflection stub.
