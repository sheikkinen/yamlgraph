# 2026-07-14 — FR-730: the taxonomy read that killed my own proposal

**Context.** I authored FR-730 with three candidate directions and a
four-code cap list, then judged it hours later. The judgement's
rubric-level verification — reading the actual inclusion terms of
every code I proposed to cap — overturned two-thirds of my own
proposal: A29's inclusion terms are genuine symptoms (falls,
drowsiness), A23 covers real exposure calls, and direction (c)'s
flagship example was self-refuting (K86's English inclusion terms can
never string-match a Finnish span — the multilingual capability the
example relies on exists precisely because nothing string-matches
catalog terms).

**Trap: author_judge_collapse, avoided by artifact.** Writing and
judging the same FR in one session invites rubber-stamping. What
prevented it was not discipline but PROCEDURE: the judgement required
reading the raw rubric rows before freezing the cap list, and the rows
disagreed with the author. read_raw_output_first generalizes beyond
model output — applied to the taxonomy itself, it is the cheapest
possible kill for a plausible mechanism (direction (c) died in one
grep, before any RED test existed).

**The satisfying part: the domain provided the mechanism.** P76-over-
P03 looked like it needed semantic machinery (evidence gating,
translation). ICPC's own practical rule 3 — "use symptom coding while
diagnostic uncertainty remains" — mechanizes to ten lines: component
from code-number ranges, demote C7 matches where a same-chapter C1
match exists. Language-independent, witnessed both directions. When a
classification standard has coding RULES, encode the rules, not
heuristics about the model's behavior.

**Honest residuals, measured:** A13 landed at the forecast's upper
bound (4/29, including one novel PRIMARY appearance on diabetic) — the
named-residual pattern from FR-727 works: the label detects it
permanently, and growth evidence (not irritation) triggers revisit.
Composition churn moved from wrong-chapter (Z50) to
within-clinical-plausible (B99 vs K86) — a defect downgraded to a
cosmetic imperfection.

**Seed:** `_component` now decodes ICPC's numbering in the reducer,
and the builder derives the same from SuperClass — two encodings of
one fact. Should the catalog rows carry `component` all the way into
candidates (loader → prompt payload → reducer) so the numbering rule
lives in exactly one place, the builder?
