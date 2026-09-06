# The loader that kept no name

**Date:** 2026-09-06
**FR:** FR-1005 (research route demotes a failed persona to a recorded row)
**Trigger:** operator, after the pi research: "investigate research failure.
FR, judge, fr, outsider, merge" — the whole rite on one defect, in one
session.

## What happened

Three research-route runs on the pi brief died on one cell each. The
investigation was cheap because the raw record was one `grep` away: run 1
put a valid enum followed by prose into `solution_class`; runs 2 and 3
overshot a 400-character cap by 71 characters, byte-identically, because
`on_error: retry` re-sends the same temperature-0 request and gets the
same answer. FR-926 had met the same class six days earlier, surfaced the
cause, and deferred the fix "until recurrence". This was the recurrence.

I drafted containment with an enum head-split and a prefix heuristic for
attributing errors to personas. The judge removed both: the head-split was
a second normalisation policy with no evidence of its own, and a prefix
heuristic is not an explicit map. It also demanded that the failure cross
the gather/reduce boundary as a Pydantic record keyed by canonical slot,
not by the model-authored `persona` cell. Run 5 then proved why: two
personas wrote a paragraph into `persona`. The human-readable names line
in the artifact is model text; the key line is the only identity.

Then the live witness failed on code every unit test had passed.
`FailedPersona` used `Literal["row_failed"]` under `from __future__ import
annotations`; the graph's Python tool loader execs the module without
registering it in `sys.modules`, and pydantic could not resolve the
deferred name. The tests loaded the same file through a helper that *did*
register it. Twenty-one witnesses green, and the first real run dead in
the first node I had touched.

## Traps

**`test_loader_is_not_the_runtime_loader`.** A module can be imported two
ways and behave two ways. The unit suite's `_load` helper inserted the
module into `sys.modules`; `load_python_function` does not. Anything that
resolves names lazily (pydantic forward refs, `get_type_hints`,
dataclass string annotations) will pass under one and die under the
other. Cure: one witness per touched module that loads it exactly as the
runtime does, and the live run before the record is written.

**`head_split_as_kindness`.** I wanted to save the run-1 row because its
head was a valid enum. The judge's point stands: the row was already
saved by containment; the split was me repairing model output because
I could, not because the contract asked. Every repair of model text is a
policy, and a policy needs its own evidence.

## Heuristic

When a reducer's promise is "demote, never drop", enumerate the places a
single row can still kill the run — the node, the gather, the validator,
the verifier — and put the floor at the one place all causes are known.
Here that was the reducer, after validation and before the first byte of
the artifact. Everything upstream records; one place decides.

**Seed:** the retry on a temperature-0 persona call is now witnessed six
times as a no-op. The framework's `on_error: retry` re-sends the identical
request. Would a retry that appends the validation error to the prompt
(FR-926's deferred "retry with error feedback") recover the fifth row
often enough to be worth an `llm` node option, and what is the first
non-research consumer that would ask for it?
