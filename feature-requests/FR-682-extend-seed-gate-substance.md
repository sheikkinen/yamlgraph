# Feature Request: Extend the diary Seed gate from presence to substance

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-07-04

## Summary

The diary-reflection content gate (`validate_diary_reflection_file` in
[scripts/gate_artifact_semantics.sh](../scripts/gate_artifact_semantics.sh#L78))
currently accepts any diary whose text contains the literal string `Seed:`.
This is a presence check, not a substance check: a line reading `Seed:` with
nothing after it passes, as does a `Seed:` buried in prose that names no
forward-looking question. This FR extends the gate to verify the Seed marker
introduces an actual seed — and to require the canonical reflection structure
the Distill rite prescribes — so the gate measures what it claims to measure.

## Value Statement

The diary is the corpus that graduates into Scripture; a gate that rubber-stamps
an empty `Seed:` lets the doctrine's most important input rot into compliance
theatre. Enforcing substance keeps the graduation pipeline fed with real seeds,
not markers.

## Problem

This is a textbook instance of the Scripture trap `gate_checks_shape_not_substance`:

> Gate validates presence (file exists, field non-empty, format matches) but not
> substance (content meaningful, cross-references valid, structural markers
> present) → compliance theatre; a 1-byte file satisfies the gate while
> conveying nothing.

FR-677 hit this directly. The diary reflection failed CI not once but twice: the
filename check, then the content check. The content check today enforces only:

1. file exists and is non-empty
2. `> 100` bytes
3. one `##` markdown header
4. the literal substring `Seed:`

None of these confirm the reflection actually reflects. Concretely, all of the
following pass the current gate while conveying nothing:

- A `Seed:` line with no question after the colon.
- A `Seed:` that restates the summary instead of posing a forward question.
- A diary with a `Seed:` marker but no Trap/Cure — i.e. a log entry wearing a
  reflection's costume, contradicting the Distill rite ("Name the cognitive
  trap or insight. Extract a heuristic. Plant a Seed.").

The cure named in Scripture is `substance_over_presence`:

> Every gate that checks 'does X exist?' must also check 'does X say something?'
> — minimum content threshold, required structural markers, or cross-reference
> validation.

## Proposed Solution

Extend `validate_diary_reflection_file` (the single shared contract, invoked by
the `diary-gate` job in `.github/workflows/commitlint.yml` and by the local
pre-commit diary hook) so the Seed check moves from presence to substance,
without becoming brittle enough to reject honest reflections.

1. **Seed must carry a question, not just a colon.** After the `Seed:` marker,
   require non-trivial content on the same line or the lines that follow — at
   minimum N characters of text and a `?` somewhere in the seed block. Reject a
   bare `Seed:` or `Seed:` followed only by whitespace.

   ```bash
   # sketch — exact regex confirmed in enforcement
   seed_block="$(sed -n '/Seed:/,$p' "$diary_file")"
   if ! printf '%s' "$seed_block" | grep -q '?'; then
     echo "::error::Seed: marker present but poses no question: $diary_label"
     return 1
   fi
   ```

2. **Require the canonical reflection sections.** The Distill rite names three
   beyond the Seed: an insight/observation, a named Trap or lesson, and a
   heuristic/Cure. Require the reflection to contain markers for the trap and
   the cure (e.g. case-insensitive `Trap` and one of `Cure`/`Heuristic`), so a
   plain changelog-style note cannot masquerade as a reflection.

3. **Keep the failure messages actionable.** Each new failure must print exactly
   what is missing and point at `docs/diary/` for a passing example, matching
   the existing gate's tone.

4. **Grandfather nothing new; validate only diaries in the PR diff.** The gate
   already runs only on `docs/diary/*reflection*fr-*` files touched by the PR
   (see `MATCHING_DIARIES`), so existing history is untouched. No sweep of old
   entries.

The exact thresholds (min seed length, which section synonyms to accept) are
deferred to enforcement and must be calibrated against the existing corpus:
regenerate the pass/fail verdict across all current `docs/diary/*reflection*`
entries and tune until every genuine reflection passes and a constructed empty
`Seed:` fails.

## Acceptance Criteria

- [ ] A diary containing a bare `Seed:` (no following question) FAILS the gate
- [ ] A diary whose Seed block contains a real forward-looking question PASSES
- [ ] A diary missing a Trap/lesson marker FAILS the gate
- [ ] A diary missing a Cure/heuristic marker FAILS the gate
- [ ] Every existing `docs/diary/*reflection*` entry that is a genuine reflection
      still PASSES (no regression sweep failures)
- [ ] Failure messages name the missing element and cite `docs/diary/`
- [ ] Unit test over `validate_diary_reflection_file` (bats or a Python harness)
      covers each new pass/fail branch, tagged with a `REQ-YG-XXX`
- [ ] `reference/` doc or `docs/confessions.md` updated only if a threshold
      warrants a noqa-style confession
- [ ] Diary reflection for this FR added

## Alternatives Considered

- **Leave the gate as presence-only.** Rejected: FR-677 proved the gate is
  already load-bearing in CI, and a presence-only marker gate is the exact
  compliance-theatre pattern Scripture condemns.
- **Replace the shell contract with an LLM judge of reflection quality.** Richer,
  but non-deterministic, slow on every commit, and over-engineered for a
  boundary check. A mechanical structural gate is the right tool; semantic
  quality review belongs to the Inquisitor, not the commit gate.
- **Enforce a strict fixed template (exact `## Observation / ## Trap / ## Cure /
  ## Seed` headers).** Rejected as too brittle — it would reject the varied but
  genuine reflection styles already in the corpus. Marker-based checks with
  synonyms tolerate style while enforcing substance.

## Related

- [scripts/gate_artifact_semantics.sh](../scripts/gate_artifact_semantics.sh#L54) — `validate_diary_reflection_file`
- [.github/workflows/commitlint.yml](../.github/workflows/commitlint.yml#L289) — `diary-gate` job
- FR-677 — the incident that exposed the presence-only gap (filename + content double failure)
- FR-373 — original shared artifact-semantics contract
- Scripture traps: `gate_checks_shape_not_substance`; cure: `substance_over_presence`
