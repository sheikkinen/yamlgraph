# 2026-07-14 — FR-725: agreement is not accuracy; the harness's first breath was a regression report

**Context.** The crosscheck harness's very first baseline (N=5 × 6
fixtures) returned 11 pass / 19 fail — and the failures agreed with
themselves perfectly: cough-fever 5/5 on `-48`, diabetic-glucose 5/5 on
`-48`. Both wrong. FR-724 had landed hours earlier with its own field
run green (HP-36 classified beautifully) and its full unit suite green.

**Trap: fixture_myopia_after_expansion.** FR-724's field check used the
fixture that MOTIVATED it (HP-36, a genuine process call) — the one
transcript where process codes SHOULD win. Nobody reran the symptom
transcripts through the expanded catalog. The regression lived exactly
in the complement of the motivating fixture. A scope expansion must
re-run the fixtures of the scope it expanded INTO, not just the one
that justified it — this is `assert_path_not_destination` at the
corpus level.

**Trap: metric_conflation.** FR-726 was framed around agreement
(variance) as the enemy. The baseline shows the classifier can be in
perfect agreement with itself and systematically wrong — bias wears
agreement as a disguise. Any stability mechanism (self-consistency
voting) would have amplified the bias with more confidence. The
kill-criterion design (close 726 if agreement ≥90%) accidentally
survives: it kills the FR for the right outcome via the wrong number.

**The domain insight that unlocked it (operator reflection):** ICPC-2
process codes are COMPONENTS — they compose with a chapter letter or
disease code (K86 + -50 → K50), they are not free-floating rivals to
symptom codes. Phase 2 put them in the arena as rivals; F4's primacy
rule then let `-48 Clarification of demand` (true of every conversation
— the Z10 of process codes) eat R05. The fix (FR-727) restores the
composition semantics: meta-process rubrics capped in code, combined
code composed mechanically from chapter_context.

**Heuristic (graduating candidate — third occurrence of the shape):**
every catalog/enum family has its "true-of-everything" members (Z10,
generic concern, -48, -69). They are detectable a priori: their rubric
describes the ENCOUNTER or the SYSTEM, not the patient's stated reason.
Cap or exclude them at the boundary BEFORE the model votes; prompt
discipline alone has now failed on this class twice in one day.

**Seed:** Could the catalog builder auto-flag "encounter-descriptor"
rubrics (title matches discussion/clarification/other-NEC/system
patterns) so the cap is data-derived rather than hand-curated — and
would that flag be a useful export for OTHER classification examples
(the pattern is universal: every taxonomy has junk-drawer codes)?
