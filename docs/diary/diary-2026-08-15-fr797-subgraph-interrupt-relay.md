# Diary — FR-797: The Demo Driver That Loved the Bug

**Date:** 2026-08-15
**Context:** FR-797 subgraph interrupt relay — LangGraph 1.x changed the child
invoke seam from *raise* (`GraphInterrupt` propagates) to *return*
(`__interrupt__` key in output). Our subgraph node kept the raise-era plumbing
(`__pregel_send` re-raise) which silently became dead code; child interrupts
were swallowed and the parent restarted the child from scratch on resume.

## Cognitive traps encountered

**boundary_contract_drift (new instance of the state boundary).** The provider
didn't change a type — it changed a *control-flow* contract: exception → value.
Every downstream assumption (pause state uncommitted, replay-by-restart) was
built on the raise semantics. The cure was the same one_law as ever: normalize
at the boundary. The two-node split exists because LangGraph only commits state
at node boundaries — committing the mapped pause state requires *returning*
from a node before *interrupting* in the next. FR-060 knew this for interrupt
nodes; the subgraph seam just hadn't caught up.

**demo_driver_encodes_the_bug.** The interrupt demo's restart heuristic
asserted `child_phase == "processing"` post-resume ⇒ FAIL. That check only
made sense *because* the old defect never committed pause-mapped state — the
demo's oracle was calibrated to the bug, so fixing the bug turned the demo red.
An assertion written against observed-buggy behavior is a regression lock on
the defect. Cure: oracles must assert the *contract* (no `__interrupt__` after
resume; final result present), not the incidental fingerprint of the current
implementation.

**denied_compound_means_nothing_ran.** The pre-command guard denied
`SKIP=pytest git commit … | tail` (pytest+tail pattern) — and because zsh
compounds are atomic under the guard, the *earlier* `printf > tmp/msg.txt`
in the same line also never ran. The next commit consumed a stale message
file. Trap: a denial is a full rollback of the line, not a partial execution;
never share a compound with a guard-sensitive fragment and a state mutation.

## What worked

- C-2 gate + rejudgement before code: the two-node split survived contact with
  the implementation unchanged — every deviation was mechanical (module
  extraction for the 450-line gate, direct conditional router instead of
  expression_edges).
- RED-first witnesses (14 tests across two files) meant the GREEN phase was
  boring; all three post-GREEN regressions were *tests asserting the refuted
  contract*, found and fixed in minutes because the suite named the seam.

## Seed

**Seed:** Demo drivers and integration oracles calibrated against observed
behavior are silent bug preservers. Could a lint detect oracle assertions that
reference implementation internals (state keys like `child_phase`) rather than
contract surfaces (`__interrupt__`, declared output mappings) — a
"contract-oracle" gate for `examples/demos/*/test_*.py`?
