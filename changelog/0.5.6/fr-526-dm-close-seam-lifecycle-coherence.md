---
type: fix
scope: examples
---
- **FR-526 DM v2 close-seam lifecycle coherence invariant**: A close seam could
  commit a `CharacterLifecycle` row that was `confirmed_dead` yet carried a non-null
  `allowed_reappearance_from_chapter` (observed in `10024-BC` Ch3) — the clamp
  reconciled the reappearance index but never the state. A new pure, packet-only
  invariant (`_enforce_reappearance_state_coherence`), applied at the close seam after
  the clamp, softens `confirmed_dead` to `missing_presumed_dead` when a reappearance is
  planned (preserving the authored return intent), leaving genuine deaths untouched.
  Defense-in-depth behind FR-525.
