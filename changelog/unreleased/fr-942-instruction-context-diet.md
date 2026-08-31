---
type: feat
scope: doctrine
req: REQ-YG-631
---
- **FR-942 Instruction Context Diet**: Combined per-turn instruction bytes (`.github/copilot-instructions.md` + `CLAUDE.md`) reduced 56,610 → 33,124 under a mechanically enforced 33,966-byte ceiling (`scripts/size_gate.py` + pre-commit `file-size-gate`). CLAUDE.md rewritten as a thin dev-command surface; env vars, branch protection, CI checks, and FR-761 dependency governance moved verbatim to `reference/development-operations.md`. 30 governed Scripture entries compressed to ≤40 words each with verbatim originals preserved in `docs/scripture-provenance.md`. Submitting Proposals section deleted from both files (operator amendment: chaplain runtime not running). (REQ-YG-631)
