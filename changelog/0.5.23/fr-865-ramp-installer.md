---
type: feat
scope: ramp
req: REQ-YG-610
---
- **FR-865 Ramp Installer**: `scripts/ramp.sh <target> --tier {1|2|3}` copies a curated, manifest-enumerated enforcement asset tree (pre-commit config, Copilot command guard, FR/judge/review skills, diary/changelog gates, capability registry shape) into a supported target repo — dry-run, idempotent skip, force-backup overwrite, target-side `docs/ramp-manifest.md` receipt, rollback, and a consumer registry in `ramp/consumers.md`. Curated assets carry drift evidence (`ramp/curation-diffs.md`) and the curated Tier-1 pre-commit config is consumed in this repo's own test path. (REQ-YG-610, REQ-YG-611, REQ-YG-612, REQ-YG-613)
