# 2026-07-13 — FR-720: the fake that lied about the interface

**Context.** Enforcing FR-720 (close LangSmith spans on race-loser cancel)
required passing `config={"run_id": ...}` to every `ainvoke`. Eight test
fakes across six files had defined `async def ainvoke(messages)` — the
LangChain Runnable interface takes `config` too, but no fake declared it
because no caller had ever passed it.

**Trap: fake_narrower_than_interface.** A test double that implements
only the subset of the interface the code currently exercises is a
time bomb with a distinctive failure signature: when the production code
starts using more of the real interface, the fake raises `TypeError` —
which the code under test correctly treats as a *candidate failure*. The
slow loser didn't hang and get cancelled; it crashed instantly and the
race "won" without cancelling anyone. Two cancellation witnesses went red
asserting "slow task must be cancelled" when the actual defect was the
fake's signature. The failure message pointed at the feature; the cause
was the double. This is `plausible_wrong_answer` inverted: a plausible
wrong FAILURE, where the assertion text describes a scenario that never
ran.

**Heuristic.** Test doubles must match the full signature of the
interface they impersonate, not the subset today's code calls — declare
unused params with defaults (`config=None`). When a previously-green
cancellation/ordering witness fails after a call-signature change, check
the doubles' signatures FIRST: a TypeError inside a gather/race is
silently converted to a candidate error and rewrites the scenario.

**Mechanism note.** Judgement F1's re-pin held up exactly: tracing is
ambient, no handle exists, so the pre-generated run_id passed as config
IS the handle; the closure enqueues `update_run` to the default executor
from inside the cancelled coroutine's except block — no await before
re-raise, verdict timing witness green unchanged.

**Seed:** Could a fixture-lint detect fakes whose `ainvoke`/`invoke`
signatures are narrower than the LangChain Runnable protocol — the same
way W-codes catch graph-schema drift — so interface-subset doubles are
flagged before a feature widens the call?
