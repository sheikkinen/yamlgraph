---
type: fix
scope: examples
---
- **FR-532 Reviewer continuity-axis calibration**: Calibrated the `book_reviewer` continuity critic against a large-model human-proxy reference over a 4-book DM sample (33 breaks). 61% of critic-flagged breaks were physical micro-state a reader glides past; all reader-real breaks were lifecycle/identity/relationship/plot. Narrowed the `continuity` system prompt to report only reader-salient breaks (de-saturating the flat 1/5 score to 4/3/2/1 on the sample) and **descoped FR-529** (the positional seam pin would fix 0 of 13 reader-real breaks). Added a reproducible calibration harness (`scripts/calibrate_continuity_axis.py`) and committed per-seam labels.
