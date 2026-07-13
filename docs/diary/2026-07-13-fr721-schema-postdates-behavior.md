# 2026-07-13 — FR-721: the schema that postdates the behavior

**Context.** Passthrough `output`/`outputs` were declared `dict[str, str]`
while the runtime's documented first branch (`resolve_template` non-string
passthrough) had accepted literal seeds for its whole life. FR-673 turned
the schema from advisory to enforced — and the enforcement gate promptly
condemned production graphs that had always been correct. ninchat's pin
alignment (NC-370) surfaced it: 8 ValidationErrors on a graph running
fine in production at 0.5.7.

**Trap: schema_as_wish, not schema_as_contract.** The type annotation
described what the author imagined the field to be, not what the runtime
did. That lie was free while the schema was advisory; the moment a gate
enforced it, every deviation became a consumer-facing break. Enforcement
does not create the bug — it collects on it, with interest, at the
consumer's boundary rather than ours.

**Heuristic.** Before any FR that flips a schema from advisory to
enforced, diff the schema against the runtime's actual tolerance — the
runtime is the incumbent contract, deployed graphs are its witnesses.
Widen the schema to the runtime (or condemn the runtime explicitly),
never enforce the wish. This is `the_one_law` seen from the other side:
the schema boundary must describe what actually crosses it.

**Mechanical note.** The fix was two type annotations; the work was the
witness — the bug report's exact payload as fixture
(read_raw_output_first), plus a guard test proving the genuinely
string-only mapping fields were NOT widened. The purge-list test is what
makes a widening safe: it pins the blast radius.

**Seed:** Could `graph lint` cross-check declared field types against
`resolve_template`'s acceptance, so a schema/runtime tolerance mismatch
is flagged before any FR enforces the schema — a W-code for "schema
narrower than runtime"?
