# 2026-07-14 — FR-724: the example that was wrong before it was written

**Context.** Phase 2 added ICPC-2 process codes. The judgement's F2
found the sharpest defect of the day: the phase-1 prompt's own
verdict-discipline example — "a medication-renewal call MATCHES the
hypertension rubric" — written 4 hours earlier as a CURE for verdict
inflation, became actively WRONG the moment the renewal process rubric
existed. The example wasn't a bug introduced by phase 2; it was a
phase-boundary assumption compiled into instruction text.

**Trap: example_encodes_coverage.** A prompt example that names a
concrete best answer silently encodes the CURRENT catalog coverage.
Every "e.g." in a prompt is a claim about the option space; when the
option space grows, yesterday's canonical example becomes today's
misdirection — and no test asserts prompt-example truth. The Judge
caught it only by asking "which phase-1 sentences become false under
phase 2?" — a question worth asking mechanically at every scope
expansion.

**Heuristic.** When an FR expands an enum/catalog/option space, grep
the prompts for examples naming members of the OLD space and re-judge
each one. Corollary for witnesses: two phase-1 tests asserted the
exclusion itself (process codes absent; coverage [1,7]) — witnesses
that pin a phase boundary must be updated as *documented obsolescence*
in the expanding FR's commit, never silently.

**Fifth fidelity shape.** The field run immediately produced a new
span-class cousin: the model drops the process-code sigil ("48" for
"-48"). Same cure family as spans: the code is a CLAIM, aligned against
the catalog at the boundary (repair when the sigiled form exists,
reject inventions). The claim-alignment pattern now covers: case-folds,
editing-by-omission, one-char inflection drift, quote-wrapping, and
sigil loss — five shapes, one boundary, zero prompt patches that held.

**Seed:** Prompt examples are load-bearing config masquerading as prose.
Could examples be EXTRACTED into the catalog/cluster brief (data, phase-
aware by construction) rather than frozen in the system prompt — so the
example for a process cluster is generated from the very rubrics the
cluster contains?
