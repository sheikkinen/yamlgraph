---
type: removal
scope: chaplain
---
- **FR-1016 FR-1012 one-shot tooling retired**: `scripts/chaplain_census.py`, `scripts/chaplain_archive.sh` and `scripts/chaplain_postmerge_witness.sh` — the census driver, the journaled subtree-archive script and the post-merge witness that executed the Chaplain removal — are deleted together with the chaplain census adapters under `examples/demos/corpus_census/adapters/` and their three test files, now that every event they served has passed. The end-state witness `tests/unit/test_fr1012_chaplain_removed.py`, the run records under `docs/census/` and CAP-264 (narrowed to the end-state claim) remain; the last complete source of the scripts is commit `36591389`, noted in `docs/archive/chaplain.md` for the repo-split work that may lift their skeleton. (REQ-YG-666)
