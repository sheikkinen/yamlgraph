---
type: fix
scope: hooks
req: REQ-YG-423
---
- **FR-1014 Dir-aware authoring guard for `graphs/`**: the FR-767 sole-route contract was flat-only for `graphs/` — `graphs/enforcement/changelog-req-check.yaml`, its prompts, and every dir-style graph FR-1011 will relocate were never governed, and the FR-767 witness tested a `.chaplain/graphs/pipeline.yaml` fixture that never existed. `governed_path()` in `pre-command-guard.sh`, `GOVERNED` in `scripts/check_authoring_proof.py`, and the `authoring-proof` hook's `files:` selector now all match `graphs/<name>/*.yaml` and `graphs/<name>/prompts/*.yaml` alongside flat `graphs/*.yaml`; the `examples/` and `.chaplain/graphs` arms are untouched. One provenance-labelled truth table (exists / FR-1011 / synthetic / negative) is witnessed on all three surfaces by `tests/unit/test_fr1014_authoring_proof_dir_graphs.py` and by the Tier-2 hook test. Phase 0 of FR-1010. (REQ-YG-423)
