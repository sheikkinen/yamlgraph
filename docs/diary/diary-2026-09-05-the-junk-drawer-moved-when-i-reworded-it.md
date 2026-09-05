# The Junk Drawer Moved When I Reworded It

**Date:** 2026-09-05
**Trigger:** FR-990 CAP journey census pilot — three runs × 30 CAPs, every
row read raw, canary gate armed. Companion: PR #589 (judge that never
says no), PR #590 (research plan), PR #591 (instrument + pilot).

## What happened, in order

1. Plan written before data: questions, closed catalog, six canaries with
   expected answers. Operator vetoed both.
2. Graph and prompt through `scripts/author.sh`; Python by hand.
3. Run 1: 25/30 judged. Two rows put a *blast_kind* value into
   `journeys`. Evidence spans failed on YAML folded scalars. Fixed in code.
4. Run 2: 28/30 judged. Every example CAP was `keep` — its own directory
   was its consumer. `author_graph` held 8 of 28 rows, 7 of them
   examples. Value column `stated` 28/28; reading `versus`: "manual X".
   Fixed in code: own-dir exclusion, enum-leak demotion, junk-drawer cap
   on examples, `extend_to` derived from a wedge map, `value_generic`.
   One prompt revision: end-user journeys, `extend` removed.
5. Run 3: 30/30 judged, 0 failed. `author_graph` dropped off the examples
   and landed on the process CAPs (changelog gate, import-linter,
   questionnaire, package seams). CAP-203 (ICPC-2) went
   `off_catalog:clinical_encounter_coding` — it was told not to say
   `author_graph` and did not recognise `census_classify` from the bare id.
6. Exit per plan §8: one rubric revision, journey canaries still miss →
   stop rewording. Remaining fixes are code and inputs, listed in FR-990.

## The trap, seen live

FR-725/727/730 named it for ICPC-2 chapters: a junk-drawer category eats
correct answers, and rewording the prompt *relocates* the junk instead of
removing it. I knew the entry. I still spent the one allowed revision on
it, and watched `author_graph` migrate from examples to tooling. The
Scripture line — "the abstraction level belongs in CODE; stop rewording"
— is not a warning about a possible failure; it is a prediction of the
exact shape the next run will take. It was right to the row.

Second, smaller: the catalog was passed as bare ids "for input closure".
That is not a catalog. ICPC-2 rubrics carry inclusion terms; a label
without a definition is a guess with a name. The model's honest
`off_catalog:clinical_encounter_coding` for an ICPC-2 example is the
proof — it had no way to know `census_classify` meant that. Input
closure was applied to the wrong thing: the *canaries* must be hidden,
the *definitions* must be shown.

## What the anchors did

The shape anchors are the success of the pilot and should be said
plainly: 30/30 valid rows; three invented consumer citations caught
(`questionnaire.py`, `map_compiler.py` for an example, a graph citing
itself) — `plausible_wrong_answer` made visible per row; two
`already_retired` correct; two genuine `retire` candidates surfaced only
after self-consumption was excluded (CAP-184; CAP-78 contested by two
`.chaplain` log hits the exclude list should have caught). Evidence
spans matched 30/30 once tolerant matching recorded *how* they matched.
None of that came from the prompt. All of it came from the reducer and
the extract.

## What I did not do

Not a fourth run. Not a third prompt wording. Not a full 242 run "to see
the matrix" — the matrix would have been built on an unstable journey
column and quoted anyway. The plan's exit criterion was written before
the data for exactly this moment, and it held.

## Heuristic

`junk_drawer_relocates_under_rewording`: when a closed-catalog label
absorbs a class of items, one prompt revision will move the absorption
to the next-nearest class, not eliminate it. The signal that you are in
this loop is a *different* set of items in the same label. Cap in code
on a property the model cannot restate (blast kind, module path), and
give the model definitions, not ids.

## Seed

The value column was `stated` 28/28 and then `generic` 10/30 after one
regex — a column that is always filled is a column that is never
checked. Should every free-text field in a census schema ship with a
falsifier (a regex, a vocabulary, a substring check) *before* the first
run, so that "always stated" is impossible by construction rather than
discovered by reading?
