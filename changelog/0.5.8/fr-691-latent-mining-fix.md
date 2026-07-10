---
type: fix
scope: examples
req: REQ-YG-530
---
- **FR-691 latent-mining fix**: the reconcile prompt now renders faction
  `internal_tensions` (previously only `description` was shown, so the miner
  could not surface tension-based threads), requires `status: latent` threads to
  carry empty `raises`/`releases`, self-checks that a zero-latent union against
  tension-loaded canon is a mining failure, and mandates non-empty `sources` on
  every thread. The Floodmark re-run now yields 3 latent threads including
  `youth_resentment` (mined from clan `internal_tensions`). `persist_threads` is
  made idempotent — a thread that leaves the union is removed from
  `story/thread/`, so the persisted set cannot drift above the cap the in-state
  gate cleared (condemned by `test_persist_removes_orphaned_threads`).
  (REQ-YG-530)
