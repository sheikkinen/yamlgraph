# FR-1076: correctness before a larger reuse surface

## Trap

The September 25-26 map review found a composition bug rather than a missing
storage abstraction. A strict map could checkpoint successes yet prevent its
downstream save from running. A cache signature based on files and model could
reuse an answer after the caller changed the rubric. Every local contract could
pass while the resulting census was wrong.

The review at `d9cfb71c` ran 50 focused tests and two compiled-map probes.
Three inputs capped to two produced `dispatched=2, met=True`; a strict map
with one failed branch retained two successes but did not run its consumer.
FR-939 subsequently closed the truncation hole. A later check at `28ec0daf`
passed 219 focused tests covering map, CLI, concurrency and demo repairs.
Those tests validate delivered code, not the reuse proposal revised here.

## Heuristic

Follow the original population, one changed semantic input and one failed
item through publication and consumption. Zero calls on run two is insufficient:
the complete key-to-classification ledger must also be correct. Publishing
outcomes is distinct from accepting them for synthesis.

This revision folds the second judgement's stable-key and reordered-input
requirements, adds explicit computation inputs and save-before-reconciliation,
and removes the generic query surface and checkpoint-size promise. It also
corrects the attribution of 10,000-item checkpoint figures to a 1,000-item test.
Results still pass through state; unpublished work still may be repeated after
interruption. Removing an unsupported promise is more useful than manufacturing
an acceptance test for it.

The main-write guard blocked this session's earlier diary attempt. This entry
settles that review debt in the isolated docs worktree, without editing the
historical judgement or granting runtime implementation authority. The revised
FR must be judged before implementation; this PR changes documentation only.

**Seed:** Can a single reusable census composition preserve useful work and
refuse stale answers without turning its result store into a query framework?
