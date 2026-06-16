# The Witness That Could Not Fail

*Diary — 2026-06-16 — FR-492 witness audit, a coda to the deterministic-Book arc*

## What happened

The witness for FR-492 (`examples/dungeon_master/scripts/witness_book_compose.py`)
had already run live against vertex and printed `=== WITNESS PASS ===`. Asked to
*check* it, I read it not for whether it passed but for whether it *could fail* —
and found it could not, at the level that matters to a machine.

Two escape hatches let `main()` return normally on a bad run, so the process
always exited 0:

1. **The substance-check FAIL printed a string and kept going.** When a chapter
   heading or its prose was missing from the book, the loop set `ok = False`,
   printed `=== WITNESS FAIL ===`, and fell off the end of `main()`. Exit 0.
2. **The incomplete-play path returned early.** If the play loop hit `TURN_CAP`
   without both chapters closing, it printed a warning and `return`ed. No PASS,
   no FAIL, exit 0 — a third, *inconclusive* state wearing success's exit code.

The only real pass signal was a human grepping stdout for the word `PASS`. The
harness around it (`EXIT=${PIPESTATUS[0]}`) was decorative: it read 0 whether the
book was faithful, malformed, or never composed at all.

The fix was three lines of `sys.exit(1)` and one explicit `=== WITNESS FAIL
(chapters did not complete within cap) ===` marker on the incomplete path. The
pass path is untouched; only the failure and inconclusive paths now color the
exit code.

## The insight: a witness is a test, and a test that cannot fail is a print statement

This is `assert_path_not_destination` turned on the witness itself. I had been
treating the script as a *demo* — something whose job is to narrate a run to a
human reading the log. But it sits in the FR's acceptance list as the **live
seam-proof** the mocked unit tests explicitly cannot give. That makes it a test,
and the first property of a test is that its failure must be *observable by the
thing that runs it* — not just legible to a person who happens to scroll. A
green exit on a red run is the `gate_checks_shape_not_substance` trap one layer
up: the gate (`EXIT=0`) checked that the script *ran*, never that it *succeeded*.

The tell I should have caught earlier: a witness whose only verdict is a printed
word can never be wired into a gate, only quoted into an FR. The moment its result
is cited as acceptance, its exit code is load-bearing — and an exit code that is
constant is not evidence.

## Seed

If this witness exits 1 on failure, what stops it from being a CI job? The
FR-474 J3 regime exempts DM from gates *because* its tests are a visibility
harness — but a witness that now fails honestly is no longer merely visibility.
Is there a third tier between "harness" and "gate": a **nightly seam-proof** that
runs the live witness, is allowed to flake on provider weather, but opens an issue
(not blocks a merge) when the *structure* fails — the heading-missing,
world-state-leaked, book-empty assertions that have nothing to do with the model's
mood? Where is the line between "the LLM wrote weak prose" (not a regression) and
"the assembly dropped a chapter" (always a regression), and can the witness be
split so only the second half is allowed to page anyone?
