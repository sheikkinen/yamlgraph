# The Engine Was Already Free; Only the Call Site Wasn't

**Date:** 2026-06-21
**FR:** FR-557 (DM v2 Contract B -- turn_engine extraction)

## What happened

`invoke_turn` fused three concerns -- prompt assembly, DM gating, and the engine
core (graph call + beat-FSM + intent normalization). The Judge had already
verified the load-bearing premise against live code: the payload handed to the
turn graph was doc-free in fact. So the extraction was re-housing, not rewriting.
I committed a golden characterization test FIRST (passing against the old code),
then moved the engine core into a new `turn_engine` module behind a typed
`TurnRequest`/`TurnResult` packet, and the golden test still passed. 345 lines
dropped to 223; the new module is 222. DM suite stayed at 404 green.

## The trap I nearly missed: the call site moved, so the test seams moved

The premise "the payload is doc-free" made the production extraction trivial. The
non-obvious cost was entirely in the **test surface**. `play_turn` now owns the
`get_app(TURN_GRAPH).ainvoke` call, so every test that monkeypatched
`turn_ops.get_app` -- six of them, across four files -- would have silently
**failed to intercept** the graph (or raised `AttributeError`, since I removed the
import from `turn_ops`). The byte-identical guarantee for *production* said nothing
about where a test injects its stub. I had to enumerate all six patch sites and
repoint them to `turn_engine.get_app`, plus move five FSM unit tests and one
`_direction_dict` test verbatim onto the new module.

The lesson: **when you extract a function that owns an external call, the
monkeypatch boundary moves with it.** A characterization test proves the data is
unchanged; it does not prove the test *harness* still points at the right seam.
Grep for the call-site name across the whole test tree before declaring the move
done -- the production diff can be perfect while half the suite stops testing what
it claims to.

## The decision I made against an acceptance criterion

The AC asked for `CastMember`/`Intent`/`Direction` as typed sub-models. I kept them
as `list[dict]`/`dict` and typed only the J2-BLOCKING `extras`. Reason: Pydantic
validating nested TypedDict/model fields can coerce or drop keys on construction,
which would risk altering the very byte-identical payload the golden test pins.
The closed `extras` kills the one untyped escape hatch the Judge flagged; the
member shapes stay documented-but-loose, with the golden test as the behavioral
contract. Typing for its own sake would have fought the behavior-preservation
mandate. I recorded this as an explicit enforce deviation in the FR rather than
silently meeting or silently skipping the criterion.

## Seed

When a refactor moves a function that owns an I/O boundary (a graph call, an HTTP
client, a file handle), can a pre-commit check enumerate the monkeypatch targets
that reference the *old* module path and flag them as orphaned -- so the "the test
no longer tests anything" failure becomes mechanical, not a thing I have to
remember to grep for?
