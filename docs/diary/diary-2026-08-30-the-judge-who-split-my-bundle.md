# Diary — 2026-08-30 — The Judge Who Split My Bundle

## What happened

Operator: "check the CI pipeline - it's running tests with 2 old pythons.
and running all tests for doc only PRs." One sentence, two defects. I
wrote one FR (FR-917) covering both. The judge returned SPLIT — correctly:
two first-consumers, two orthogonal surfaces, one FR. The split children
(FR-918 matrix, FR-919 doc-only skip) each came back APPROVED WITH
REVISIONS, revisions folded, both enforced the same day.

## Traps encountered

- **Bundle-as-single-FR.** The operator's sentence had an "and" in it and
  I carried the "and" into the FR. The judge's SPLIT was mechanical
  doctrine (orthogonal concerns), but I could have caught it at authoring
  time by counting first-consumers: two first events = two FRs. The
  conjunction in a task statement is a split hint, not a scope statement.
- **Exact-set overclaim (FR-918 R-1).** I wrote "every supported
  interpreter is exercised by CI" while deliberately leaving 3.12
  classified but leg-less. The judge caught the contradiction between my
  rhetoric and my own matrix. Bracket policy (floor + ceiling, intermediates
  supported by bracket) was what I meant; I wrote the stronger claim
  because it sounded cleaner. Plausible wrong *prose* is the FR-authoring
  analogue of plausible_wrong_answer.
- **Output-safe is not step-safe (FR-919 R-1).** My gate expression
  short-circuited on non-PR events, but the filter *step* still executed
  on tag pushes — a step failure there would break the release chain even
  though the output would have been correct. Guards must be applied at the
  step that can fail, not only at the value that is read.
- **Hook false positive: context lines are not changes.** The
  changelog-release-sync gate greps the staged pyproject.toml *diff* for
  `version = "` — my `requires-python` edit put the version field into
  the hunk's context lines and tripped the gate with zero version change.
  Verified (`grep -c` = 1 context occurrence), skipped that single hook
  with a recorded rationale. The gate checks shape (string in diff), not
  substance (line actually changed) — gate_checks_shape_not_substance,
  inverted: here the shape check *over*-fires.

## What worked

- The judge-then-fold loop was cheap: three judge runs, all revisions
  mechanically foldable, no re-judgement needed for APPROVED WITH
  REVISIONS verdicts.
- Single-glob classifier (`!**/*.md`) instead of a directory allowlist —
  the dorny OR-semantics trap was killed in the alternatives table before
  any YAML existed (spec_kill).

## Seed

Could the FR template's "First consumer / first event" field mechanically
reject plural answers? A pre-commit check that counts "first event"
phrases (or `; and` in that field) would move the SPLIT verdict from the
judge (expensive) to the author's editor (free) — the same migration that
two_strike_split prescribes: from instruction text to code.
