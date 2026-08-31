# The Doctrine That Ate Its Own Context

**Date:** 2026-08-31
**FR:** FR-942 (instruction context diet)

## What happened

The two per-turn instruction files had grown to 56,610 bytes — a fifth of
a compaction budget spent before the first user word. FR-942 put them on
a diet: CLAUDE.md became a thin dev-command surface, operational detail
moved verbatim to `reference/development-operations.md`, thirty governed
Scripture entries were compressed to ≤40 words with originals preserved
in `docs/scripture-provenance.md`, and a 33,966-byte combined ceiling now
lives in the same size gate that enforces the 450-line law. Landed at
33,124 bytes.

## The trap I walked into

**Doc-pinning tests are load-bearing walls in a move.** The GREEN commit
looked done — 19/19 acceptance tests passed — until the pre-commit full
suite surfaced 27 collateral failures across ten files. Every one was a
prior FR's witness pinning instruction-file content I had relocated or
deleted: branch-protection assertions, CI-check lists, the chaplain-inbox
section, the coverage-threshold cross-check, even a compressed Scripture
clause that had silently dropped `yamlgraph graph list` — a token another
FR's test (FR-910) existed specifically to protect. The acceptance suite
tested the *new* contract; the repo's memory tested the *old* one. Neither
alone was the truth.

The Scripture already names this: `partial_remediation` — fix all
occurrences, not just the cited one. The refinement worth recording is
that for a *content relocation*, the occurrences are not in the moved
text but in the tests that point at it. The FR's own acceptance criteria
can be 100% green while the enforcement ring around *other* FRs is red.

## The cure that worked

Repoint, don't weaken. Each collateral test followed its content to the
new canonical location (`development-operations.md`); the chaplain-inbox
witnesses inverted into retirement witnesses (operator amendment: the
chaplain runtime is not running, so Submitting Proposals died in both
files rather than deduplicating into one). No assertion was deleted
without a successor pinning the new truth. The compression that dropped
FR-910's protected token was restored *within* the 40-word cap — the two
constraints were compatible once both were visible.

## One number worth keeping

The provenance cross-check (diff governed entries against origin/main,
set-compare with `docs/scripture-provenance.md` records) found exactly
30 changed / 0 missing / 0 extra on first run — because it was written
as a script, not eyeballed. A five-minute verification script beats an
hour of manual diff reading, and it becomes the AC-12 evidence for free.

**Seed:** Doc-pinning tests form an undeclared dependency graph on
instruction-file *sections*. Could the size gate (or a lint) extract
every string literal that tests assert against instruction files, and
report which sections are load-bearing *before* an edit — a
`who_reads_this_when` answered mechanically, at edit time rather than
at pre-commit time?
